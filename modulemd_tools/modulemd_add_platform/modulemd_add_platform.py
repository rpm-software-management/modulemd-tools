#!/usr/bin/python3
import sys
import argparse
import logging
import os
from pathlib import Path
import re
import tempfile
import gi

gi.require_version('Modulemd', '2.0')
from gi.repository import Modulemd  # noqa: E402

# YAML backslash escape to Unicode charater mapping
yaml_escapes = {
    '0': '\0',
    'a': '\a',
    'b': '\b',
    't': '\t',
    'n': '\n',
    'v': '\v',
    'f': '\f',
    'r': '\r',
    'e': '\u001B',
    '"': '"',
    '/': '/',
    '\\': '\\',
    'N': '\u0085',
    '_': '\u00A0',
    'L': '\u2028',
    'P': '\u2029'
}
# Unicode to YAML backslash escape mapping for double-quoted strings
yaml_deescapes = {
    '\0': '\\0',
    '\a': '\\a',
    '\b': '\\b',
    '\t': '\\t',
    '\n': '\\n',
    '\v': '\\v',
    '\f': '\\f',
    '\r': '\\r',
    '\u001B': '\\e',
    '"': '\\"',
    '\\': '\\\\',
    '\u0085': '\\N',
    '\u00A0': '\\_',
    '\u2028': '\\L',
    '\u2029': '\\P'
}


def dequote_yaml_string(input):
    """Remove string separators from a YAML string scalar.

    Return a string value, a quoting style, and a comment suffix used in the
    string. Quoting style is a double quote, a single quote, an empty string
    (for no quoting). This function assumes valid YAML.

    E.g. If an input is "'FOO'#comment", output will be ("FOO", "'", "#comment").
    In case of error returns (None, None, None).
    """
    # Double-quoted?
    result = re.match(r'^\s*"(.*)', input)
    if result:
        escape = False
        in_suffix = False
        hexleft = 0
        output = ''
        suffix = ''
        for character in result.group(1):
            if in_suffix:
                suffix += character
                continue
            if hexleft > 0:
                hexleft -= 1
                hexvalue <<= 4
                hexvalue += int(character, base=16)
                if hexleft == 0:
                    output += chr(hexvalue)
                continue
            if escape:
                escape = False
                # \xHH, \uHHHH, \UHHHHHHHH
                if character == 'x':
                    hexleft = 2
                    hexvalue = 0
                elif character == 'u':
                    hexleft = 4
                    hexvalue = 0
                elif character == 'U':
                    hexleft = 8
                    hexvalue = 0
                else:
                    output += yaml_escapes[character]
                continue
            if character == '\\':
                escape = True
                continue
            if character == '"':
                in_suffix = True
                continue
            output += character
        return (output, '"', suffix)
    # Single quoted?
    result = re.match(r'^\s*\'(.*)', input)
    if result:
        quoted = False
        in_suffix = False
        output = ''
        suffix = ''
        for character in result.group(1):
            if in_suffix:
                suffix += character
                continue
            if quoted:
                quoted = False
                if character == "'":
                    output += "'"
                    continue
                else:
                    in_suffix = True
                    suffix += character
                    continue
            if character == "'":
                quoted = True
                continue
            output += character
        return (output, "'", suffix)
    # Unquoted?
    result = re.match(r'^\s*([^#]*[^#\s])(\s*(?:#.*)?)', input)
    if result:
        return (result.group(1), '', result.group(2))
    # Error.
    return (None, None, None)


def quote_yaml_string(value, style, suffix):
    """Quote a string using the given style, append a comment suffix,
    and return the quoted YAML scalar. This is a reverse of dequote_yaml_string().

    Be ware that if the value contains characters forbidden in the requested
    quoting style, this function will produce a double-quoted string instead
    which is the most expressive style.

    E.g. if an input is ('FOO', '"', '#comment'), the output will be
    '"FOO"#comment'.
    """
    # Switch style if needed.
    # Printable line-oriented characters (e.g. '\n', '\r') excluded on purpose
    if not re.match(
            r'\A[\x20-\x7E\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]*\Z',
            value):
        style = '"'
    if (style == '' and (
            re.match(r"\A[\s'\"]", value) or re.match(r"\s\Z", value) or re.match("[#:]", value))):
        style = '"'

    # Format without quotes
    if style == '':
        return value + suffix
    # Format with single-quotes
    if style == "'":
        output = ''
        for character in value:
            if character == "'":
                output += "''"
                continue
            output += character
        return "'" + output + "'" + suffix
    # Else default to double quotes
    output = ''
    for character in value:
        if character in yaml_deescapes:
            output += yaml_deescapes[character]
        elif not re.match(
                r'[\x20-\x7E\xA0-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]',
                value):
            output += '\\U{:08X}'.format(ord(character))
        else:
            output += character
    return '"' + output + '"' + suffix


def edit(logger, content, old_platform, new_platform, context_map):
    """Manually add build configurations in YAML document.

    Content is a modulemd-packager-v3 YAML document with contexts of for
    old_plaform. This function duplicates contexts listed in context_map keys
    to new contexts listed in context_map values. When duplicating, it will
    rewrite old_platform to new_platform.
    """
    output = []
    record = []
    in_configurations = False
    in_context = False
    current_context = ''
    this_context_is_old_platform = False
    for line in content.splitlines():
        logger.debug('INPUT: %s', line)
        output.append(line)

        # Comments can interleave disrespecting indentation
        if re.match(r'^\s*#', line):
            if in_context:
                record.append(line)
            continue

        if in_context:
            result = re.match(
                r'^' + indent_configurations + indent_context,
                line)
            if result:
                result = re.match(r'^(' + indent_configurations
                                  + indent_context + r'platform\s*:\s*)([\'"\S].*)', line)
                if result:
                    platform, style, suffix = dequote_yaml_string(result.group(2))
                    if platform == old_platform:
                        logger.debug('HIT old platform')
                        this_context_is_old_platform = True
                        line = result.group(1) \
                            + quote_yaml_string(new_platform, style, suffix)
                record.append(line)
                continue
            else:
                in_context = False
                logger.debug('END context "%s"', current_context)
                for x in record:
                    logger.debug('RECORDED: %s', x)
                if current_context in context_map:
                    # Insert the recorded context before the last output line
                    for x in record:
                        output.insert(-1, x)

        if in_configurations:
            # TODO: Handle "-\n context". Comments can interleave.
            result = re.match(
                r'^(' + indent_configurations + r'(\s*)-(\s+)context\s*:\s*)(.*)',
                line)
            if result:
                in_context = True
                context_value_prefix = result.group(1)
                indent_context = result.group(2) + ' ' + result.group(3)
                current_context, current_context_style, \
                    current_context_suffix = dequote_yaml_string(result.group(4))
                record.clear()
                if current_context in context_map:
                    record.append(context_value_prefix + quote_yaml_string(
                        context_map[current_context], current_context_style,
                        current_context_suffix))
                logger.debug('START context "%s"', current_context)
            continue

        # TODO: Restrict the space prefix to a second level
        result = re.match(r'^(\s+)configurations\s*:', line)
        if result:
            in_configurations = True
            indent_configurations = result.group(1)
            logger.debug('START configurations')
            continue

    # If the old context block was right at the end of the document.
    if in_context:
        in_context = False
        logger.debug('END context "%s" at end of document', current_context)
        for x in record:
            logger.debug('RECORDED: %s', x)
        if current_context in context_map:
            # Append the recorded context after the last output line
            for x in record:
                output.append(x)

    # Accaunt for the end-of-line character of the last line.
    if content.endswith('\n'):
        logger.debug('Appending final new line')
        output.append('')

    return '\n'.join(output)


def equaled_modulemd_packager(a, b):
    """Compare two modulemd-packager documents.

    Return true if equaled. False otherwise. It modifies the documents.
    """
    # convert_to_index() requires mandatory fields (e.g. summary) to be set.
    # It seems that validation in packager_read_*() has a bug.
    for document in a, b:
        document.set_summary('dummy')
        document.set_description('dummy')
    return a.convert_to_index().dump_to_string() \
        == b.convert_to_index().dump_to_string()


def generate_context(contexts):
    """Generate a new string which does not exist in the given list."""
    for integer in range(sys.maxsize):
        context = '{!s}'.format(integer)
        if context not in contexts:
            return context


def validate_context(context):
    """Check the given string is a valid context.

    Return True if it valid, False otherwise.
    (libmodulemd does not yet export the validation function. This our own
    implementation.)
    """
    return re.match(r'^[A-Za-z0-9]{1,10}$', context)


def duplicate_configuration(template_configuration, new_context, new_platform):
    """Copy a template configuration, set the new context, and return it."""
    new_configuration = template_configuration.copy()
    new_configuration.set_context(new_context)
    new_configuration.set_platform(new_platform)
    return new_configuration


def process_string(logger, content, ignore_unsuitable, old_platform,
                   new_platform):
    """Add a configuration for a new platform to the modulemd document string.

    It returns an error code and a string.
    In case of no error, code will be 0 and the string will be the processed,
    output document.
    In case of an error, code will be nonzero and the string will contain an
    error message.
    A special error -1 means the document needs no editing. Either because it
    already contains a configuration the new platform, or because
    ignore_unsuitable argument is True and the string does not contain
    a configuration for the old platform or the string is a modulemd-v2
    document, which does not use configurations.
    """

    # Parse and validate the content
    try:
        document = Modulemd.read_packager_string(content)
    except Exception as e:
        return 1, 'Unable to parse a modulemd-packager document: {}'.format(e)
    # Ignore unsuitable documents if requested
    if type(document) == Modulemd.ModuleStreamV2:
        return -1 if ignore_unsuitable else 1, 'This is a modulemd-v2 document'

    # Enumerate all contexts with the old platform
    contexts = document.get_build_config_contexts_as_strv()
    template_configurations = []
    for context in contexts:
        configuration = document.get_build_config(context)
        if configuration.get_platform() == new_platform:
            # If there is already a context for the new platform,
            # there no work for us.
            return -1, 'A context for the new {} platform already exists: {}' \
                .format(configuration.get_context(), new_platform)
        if configuration.get_platform() == old_platform:
            template_configurations.append(configuration)

    # Duplicate configurations
    new_configurations = []
    old_to_new_context_map = {}
    if len(template_configurations) == 0:
        return -1 if ignore_unsuitable else 2, \
            'No context with the old platform {}.'.format(old_platform)
    elif len(template_configurations) == 1:
        # Try using the new platform as the new context
        if new_platform in contexts:
            new_context = generate_context(contexts)
        elif not validate_context(new_platform):
            new_context = generate_context(contexts)
        else:
            new_context = new_platform
        new_configurations.append(duplicate_configuration(
            template_configurations[0], new_context, new_platform))
        contexts.append(new_context)
        old_to_new_context_map[template_configurations[0].get_context()] = \
            new_context
    else:
        for template_configuration in template_configurations:
            new_context = generate_context(contexts)
            new_configurations.append(duplicate_configuration(
                template_configuration, new_context, new_platform))
            contexts.append(new_context)
            old_to_new_context_map[template_configuration.get_context()] = \
                new_context
    for new_configuration in new_configurations:
        document.add_build_config(new_configuration)

    # Edit the document preserving formatting
    edited_content = edit(logger, content, old_platform, new_platform,
                          old_to_new_context_map)

    # Reparse the document to verify it was not damaged
    try:
        edited_document = Modulemd.read_packager_string(edited_content)
    except Exception as e:
        return 3, 'Unable to parse the edited document: {}:\n{}'.format(e, edited_content)

    # Compare library-edited and manually edited documents
    if not equaled_modulemd_packager(document, edited_document):
        return 4, \
            'Editing would demage the modulemd-packager document:\n{}'.format(edited_content)

    return 0, edited_content


def process_file(logger, file, stdout, skip, old_platform, new_platform):
    """Add a configuration for a new platform to the modulemd file.

    The file is overwritten if stdout is False. Otherwise, the file is left
    intact and the modified content is printed.

    The file should be a modulemd-packager document with a context for the old
    platform. If it isn't and a skip argument is False, an error will be
    reported. Otherwise the file will be skipped. Nevertheles if the file
    already contains a context for the new platform, the file will also be
    skipped.

    In case of an error, return (True, an error message).
    In case of success, return (False, a warning), where the warning is an
    optinal notification the user could be interrested in.
    """

    # Open the modulemd-packager file
    try:
        fd = open(file, encoding='UTF-8')
    except Exception as e:
        return (True,
                'Could not open the modulemd-packager file: {}'.format(e))
    # Read the file
    try:
        content = fd.read()
    except Exception as e:
        fd.close()
        return (True,
                '{}: Could not read the modulemd-packager file: {}'.format(
                    file, e))
    if not stdout:
        # Retrieve permissions of the file
        try:
            stat = os.fstat(fd.fileno())
        except Exception:
            fd.close()
            return (True,
                    '{}: Could not stat the modulemd-packager file: {}'.format(file, e))
    # Close the file
    fd.close()

    # Edit the document in memory
    error, text = process_string(logger, content, skip, old_platform,
                                 new_platform)
    if error == -1:
        return (False, '{}: Skipped: {}'.format(file, text))
    elif error:
        return (True, '{}: {}'.format(file, text))

    # Print the edited document to a standard output
    if stdout:
        try:
            sys.stdout.write(text)
        except Exception as e:
            return (True,
                    '{}: Could not write to a standard output: {}'.format(e))
        return (False, None)

    # Or store the edited document into a temporary file
    try:
        temp_fd, temp_name = tempfile.mkstemp(dir=Path(file).parent, text=True)
        temp_file = os.fdopen(temp_fd, mode='w', encoding='UTF-8')
        temp_file.write(text)
    except Exception as e:
        temp_file.close()
        return (True,
                '{}: Could not write to a temporary file: {}'.format(
                    temp_name, e))
    # Copy file permissions
    try:
        os.fchmod(temp_fd, stat.st_mode)
    except Exception as e:
        temp_file.close()
        return (True,
                '{}: Could not copy a file mode: {}'.format(temp_name, e))
    try:
        os.fchown(temp_fd, stat.st_uid, stat.st_gid)
    except Exception as e:
        temp_file.close()
        return (True,
                '{}: Could not copy a file ownership: {}'.format(temp_name, e))
    # Close the descriptor
    try:
        temp_file.close()
    except Exception as e:
        return (True, '{}: Could not close the file: {}'.format(temp_name, e))
    # And replace the file
    try:
        os.replace(temp_name, file)
    except Exception as e:
        return (True, '{}: Could not rename to {}: {}'.format(temp_name, file, e))

    # Successfully stored
    return (False, None)


def main():
    arg_parser = argparse.ArgumentParser(
        description='Add a context for the given platform.')
    arg_parser.add_argument('file', metavar='FILE',
                            help='A file with modulemd-packager document to edit')
    arg_parser.add_argument('--old', required=True, metavar='PLATFORM',
                            help='old platform')
    arg_parser.add_argument('--new', required=True, metavar='PLATFORM',
                            help='new platform')
    arg_parser.add_argument('--skip', action='store_true',
                            help='ignore documents without a context for the old platform '
                            'and modulemd-v2 documents')
    arg_parser.add_argument('--stdout', action='store_true',
                            help='print the editted document to a standard output instead of '
                            'rewriting the FILE')
    arg_parser.add_argument('--debug', action='store_true',
                            help='Log parsing and editting')
    arguments = arg_parser.parse_args()

    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    if arguments.debug:
        logger.setLevel(level=logging.DEBUG)
    # TODO: Validate platform values
    error, message = process_file(logger, arguments.file, arguments.stdout,
                                  arguments.skip, arguments.old, arguments.new)
    if error:
        sys.stderr.write('Error: {}\n'.format(message))
        exit(1)
    if message:
        sys.stderr.write('{}\n'.format(message))
    exit(0)


if __name__ == '__main__':
    main()
