#!/usr/bin/python3
import sys
import argparse
import os
from pathlib import Path
import re
import stat
import tempfile
import gi
gi.require_version('Modulemd', '2.0')
from gi.repository import Modulemd

def dequote_yaml_string(input):
    """Remove string separators from a YAML string scalar.

    E.g. input is "'FOO'", output is "FOO". In case of error returns None.
    """
    # TODO: backslash escaping
    result = re.match(r'^\s*"([^"]*)"', input)
    if result:
        return result.group(1)
    result = re.match(r'^\s*\'([^\']*)\'', input)
    if result:
        return result.group(1)
    result = re.match(r'^\s*([^"\'#]+)', input)
    if result:
        return result.group(1)

def edit(content, old_platform, new_platform, context_map):
    """Manually add build configurations in YAML document.

    Content is a modulemd-packager-v3 YAML document with contexts of for
    old_plaform. This function duplicates contexts listed in context_map keys
    to new contexts listed in context_map values. When duplicating, it will
    rewrite old_platform to new_platform.
    """
    # TODO: There can be multiple contexts for a platform. All of them should
    # be duplicated.
    output = []
    record = []
    contexts = []
    in_configurations = False
    in_context = False
    current_context = ''
    this_context_is_old_platform = False
    new_context_starts_at_line_number = -1;
    old_context_lines = []
    for line in content.splitlines():
        print(line)
        output.append(line)

        # Comments can interleave disrespecting indentation
        if re.match(r'^\s*#', line):
            if in_context:
                record.append(line)
            continue

        if in_context:
            result = re.match(
                    r'^' + indent_configurations + indent_context + r'\S',
                    line)
            if result:
                result = re.match(
                        r'^(\s+platform\s*:\s*)([\'"]?)' + old_platform +
                            r'(\2)(\s.*|#.*|$)',
                        line)
                if result:
                    print('HIT old platform')
                    this_context_is_old_platform = True
                    line = result.group(1) + result.group(2) + new_platform \
                            + result.group(2)
                record.append(line)
                continue
            else:
                in_context = False
                print('END context of ' + current_context)
                for x in record:
                    print('RECORDED: ' + x)
                if current_context in context_map:
                    # Insert the recorded context in before the last output line
                    for x in record:
                        output.insert(-1, x)

        if in_configurations:
            # TODO: Handle "-\n context". Comments can interleave.
            result = re.match(
                    r'^(' + indent_configurations +
                        r'(\s*)-(\s+)context\s*:\s*)(\S+)',
                    line)
            if result:
                in_context = True
                context_value_prefix = result.group(1)
                indent_context = result.group(2) + ' ' + result.group(3)
                current_context = dequote_yaml_string(result.group(4))
                contexts.append(current_context)
                record.clear()
                if current_context in context_map:
                    record.append(context_value_prefix + "'"
                            + context_map[current_context] +"'")
                print('START context "{}"'.format(current_context))
            continue

        # TODO: Restrict the space prefix to a second level
        result = re.match(r'^(\s+)configurations\s*:', line)
        if result:
            in_configurations = True
            indent_configurations = result.group(1)
            print('START configurations')
            continue

    print('OUTPUT:')
    for line in output:
        print(line)

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

def process_string(content, old_platform, new_platform):
    """Add a configuration for a new platform to the modulemd document string.

    It returns an error code and a string.
    In case of no error, code will be 0 and the string will be the processed,
    output document.
    In case of an error, code will be nonzero and the string will contain an
    error message.
    A special error -1 means the document needs no editing.
    """

    # Parse and validate the content
    try:
        document = Modulemd.read_packager_string(content)
    except Exception as e:
        return 1, 'Unable to parse a modulemd-packager document: {}'.format(e)

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
        return 2, 'No context with the old platform {}.'.format(old_platform)
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
    edited_content = edit(content, old_platform, new_platform,
            old_to_new_context_map)

    # Reparse the document to verify it was not damaged
    try:
        edited_document = Modulemd.read_packager_string(edited_content)
    except Exception as e:
        return 3, 'Unable to parse the edited document: {}'.format(e)

    # Compare library-edited and manually edited documents
    if not equaled_modulemd_packager(document, edited_document):
        return 4, 'Editing would demage the modulemd-packager document.'

    return 0, edited_content

def process_file(file, stdout, old_platform, new_platform):
    """Add a configuration for a new platform to the modulemd file.

    The file is overwritten if stdout is False. Otherwise, the file is left
    intact and the modified content is printed.

    In case of error, return (True, an error message).
    In case of success, return (False, a warning), where the warning is an
    optinal notification the use could be interrested in.
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
        except:
            fd.close()
            return (True,
                    '{}: Could not stat the modulemd-packager file: {}'.format(
                    file, e))
    # Close the file
    fd.close()

    # Edit the document in memory
    error, text = process_string(content, old_platform, new_platform)
    if error == -1:
        return (False, '{}: Skipped: {}'.format(file, text))
    elif error:
        return (True, '{}: {}'.format(file, text))
    # TODO: Handle soft errors by printing/keeping the edited text (damage etc.)

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
                '{}: Could not copy a file ownership: {}'.format(temp_name,
                    e))
    # Close the descriptor
    try:
        temp_file.close()
    except Exception as e:
        return (True, '{}: Could not close the file: {}'.format(temp_name, e))
    # And replace the file
    try:
        os.replace(temp_name, file)
    except Exception as e:
        return (True, '{}: Could not rename to {}: {}'.format(temp_name, file,
            e))

def main():
    arg_parser = argparse.ArgumentParser(
        description = 'Add a context for the given platform')
    arg_parser.add_argument('file', metavar='FILE',
            help='A file with packager-modulemd document to edit')
    arg_parser.add_argument('--old', required=True, metavar='PLATFORM',
            help='old platform')
    arg_parser.add_argument('--new', required=True, metavar='PLATFORM',
            help='new platform')
    arg_parser.add_argument('--stdout', action='store_true',
            help='print the editted document to a standard output instead of'
                'rewriting the FILE')
    arguments = arg_parser.parse_args()
    # TODO: Validate platform values
    error, message = process_file(arguments.file, arguments.stdout,
            arguments.old, arguments.new)
    if error:
        sys.stderr.write('Error: {}\n'.format(message))
        exit(1)
    if message:
        sys.stderr.write('{}\n'.format(warning))
    exit(0)


if __name__ == '__main__':
    main()
