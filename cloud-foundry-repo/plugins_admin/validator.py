"""
Plugin validator class

"""
import zipfile
import base64
import re
import os
import ConfigParser
import StringIO
import codecs
from plugin_exceptions import ValidationError
import settings

PLUGIN_MAX_UPLOAD_SIZE=getattr(settings, 'PLUGIN_MAX_UPLOAD_SIZE', 1048576)
PLUGIN_REQUIRED_METADATA=getattr(settings, 'PLUGIN_REQUIRED_METADATA', ('name', 'description', 'version', 'qgisMinimumVersion', 'author', 'email', 'about', 'tracker', 'repository'))

PLUGIN_OPTIONAL_METADATA=getattr(settings, 'PLUGIN_OPTIONAL_METADATA', ( 'homepage', 'changelog', 'qgisMaximumVersion', 'tags', 'deprecated', 'experimental', 'external_deps', 'server'))
PLUGIN_BOOLEAN_METADATA=getattr(settings, 'PLUGIN_BOOLEAN_METADATA', ('experimental', 'deprecated', 'server'))


def _read_from_init(initcontent, initname):
    """
    Read metadata from __init__.py, raise ValidationError
    """
    metadata = []
    i = 0
    lines = initcontent.split('\n')
    while i < len(lines):
        if re.search('def\s+([^\(]+)', lines[i]):
            k = re.search('def\s+([^\(]+)', lines[i]).groups()[0]
            i += 1
            while i < len(lines) and lines[i] != '':
                if re.search('return\s+["\']?([^"\']+)["\']?', lines[i]):
                    metadata.append((k, re.search('return\s+["\']?([^"\']+)["\']?', lines[i]).groups()[0]))
                    break
                i += 1
        i += 1
    if not len(metadata):
        raise ValidationError('Cannot find valid metadata in %s' % initname)
    return metadata

def _check_required_metadata(metadata):
    """
    Checks if required metadata are in place, raise ValidationError if not found
    """
    for md in PLUGIN_REQUIRED_METADATA:
        if not md in dict(metadata) or not dict(metadata)[md]:
            raise ValidationError('Cannot find metadata <strong>%s</strong> in metadata source <code>%s</code>.<br />For further informations about metadata, please see: <a target="_blank"  href="http://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins.html#plugin-metadata-table">metadata documentation</a>' % (md, dict(metadata).get('metadata_source')))


def validator(package):
    """
    Analyzes a zipped file, returns metadata if success, False otherwise.
    If the new icon metadata is found, an inmemory file object is also returned

    Current checks:

        * size <= PLUGIN_MAX_UPLOAD_SIZE
        * zip contains __init__.py in first level dir
        * mandatory metadata: ('name', 'description', 'version', 'qgisMinimumVersion', 'author', 'email')
        * package_name regexp: [A-Za-z][A-Za-z0-9-_]+
        * author regexp: [^/]+

    """
    try:
        if package.size > PLUGIN_MAX_UPLOAD_SIZE:
            raise ValidationError("File is too big. Max size is %s Bytes" % PLUGIN_MAX_UPLOAD_SIZE )
    except AttributeError:
        try:
            if package.len > PLUGIN_MAX_UPLOAD_SIZE:
                raise ValidationError("File is too big. Max size is %s Bytes" % PLUGIN_MAX_UPLOAD_SIZE )
        except AttributeError:
            try:
                if len(package.stream.read()) > PLUGIN_MAX_UPLOAD_SIZE:
                    raise ValidationError("File is too big. Max size is %s Bytes" % PLUGIN_MAX_UPLOAD_SIZE )
            except AttributeError:
                try:
                    if os.fstat(package.fileno()).st_size > PLUGIN_MAX_UPLOAD_SIZE:
                        raise ValidationError("File is too big. Max size is %s Bytes" % PLUGIN_MAX_UPLOAD_SIZE )
                except AttributeError:
                    if len(package.read()) > PLUGIN_MAX_UPLOAD_SIZE:
                        raise ValidationError("File is too big. Max size is %s Bytes" % PLUGIN_MAX_UPLOAD_SIZE )
                    else:
                        package.seek(0)


    try:
        zip = zipfile.ZipFile(package)
    except:
        raise ValidationError("Could not unzip file.")
    for zname in zip.namelist():
        if zname.find('..') != -1 or zname.find(os.path.sep) == 0 :
            raise ValidationError("For security reasons, zip file cannot contain path informations")
    bad_file = zip.testzip()
    if bad_file:
        zip.close()
        del zip
        try:
            raise ValidationError('Bad zip (maybe a CRC error) on file %s' %  bad_file)
        except UnicodeDecodeError:
            raise ValidationError('Bad zip (maybe unicode filename) on file %s' %  unicode( bad_file, errors='replace'))

    # Checks that package_name  exists
    namelist = zip.namelist()
    try:
        package_name = namelist[0][:namelist[0].index('/')]
    except:
        raise ValidationError("Cannot find a folder inside the compressed package: this does not seems a valid plugin")

    # Cuts the trailing slash
    if package_name.endswith('/'):
        package_name = package_name[:-1]
    initname = package_name + '/__init__.py'
    metadataname = package_name + '/metadata.txt'
    if not initname in namelist and not metadataname in namelist:
        raise ValidationError('Cannot find __init__.py or metadata.txt in the compressed package: this does not seems a valid plugin (I searched for %s and %s)' % (initname, metadataname))

    # Checks for __init__.py presence
    if not initname in namelist:
        raise ValidationError("Cannot find __init__.py in plugin package.")

    # Checks metadata
    metadata = []
    # First parse metadata.txt
    if metadataname in namelist:
        try:
            parser = ConfigParser.ConfigParser()
            parser.optionxform = str
            parser.readfp(StringIO.StringIO(codecs.decode(zip.read(metadataname), "utf8")))
            if not parser.has_section('general'):
                raise ValidationError("Cannot find a section named 'general' in %s" % metadataname)
            metadata.extend(parser.items('general'))
        except Exception, e:
            raise ValidationError("Errors parsing %s. %s" % (metadataname, e))
        metadata.append(('metadata_source', 'metadata.txt'))
    else:
        # Then parse __init__
        # Ugly RE: regexp guru wanted!
        initcontent = zip.read(initname)
        metadata.extend(_read_from_init(initcontent, initname))
        if not metadata:
            raise ValidationError('Cannot find valid metadata in %s' % initname)
        metadata.append(('metadata_source', '__init__.py'))

    _check_required_metadata(metadata)

    # Process Icon
    try:
        # Strip leading dir for ccrook plugins
        if dict(metadata)['icon'].startswith('./'):
            icon_path = dict(metadata)['icon'][2:]
        else:
            icon_path = dict(metadata)['icon']
        icon = zip.read(package_name + '/' + icon_path)
        icon_content = base64.b64encode(icon)
    except:
        icon_content = ''

    metadata.append(('icon_content', icon_content))
    metadata.append(('icon', icon_path))
    del dict(metadata)['icon']

    # Transforms booleans flags (experimental)
    for flag in PLUGIN_BOOLEAN_METADATA:
        if flag in dict(metadata):
            metadata[metadata.index((flag, dict(metadata)[flag]))] = (flag, dict(metadata)[flag].lower() == 'true' or dict(metadata)[flag].lower() == '1')

    # Adds package_name
    if not re.match(r'^[A-Za-z][A-Za-z0-9-_]+$', package_name):
        raise ValidationError("The name of the top level directory inside the zip package must start with an ASCII letter and can only contain ASCII letters, digits and the signs '-' and '_'.")
    metadata.append(('package_name', package_name))

    # Last temporary rule, check if mandatory metadata are also in __init__.py
    # fails if it is not
    min_qgs_version = dict(metadata).get('qgisMinimumVersion')
    max_qgs_version = dict(metadata).get('qgisMaximumVersion')
    if tuple(min_qgs_version.split('.')) < tuple('1.8'.split('.')) and metadataname in namelist:
        initcontent = zip.read(initname)
        try:
            initmetadata = _read_from_init(initcontent, initname)
            initmetadata.append(('metadata_source', '__init__.py'))
            _check_required_metadata(initmetadata)
        except ValidationError, e:
            raise ValidationError("qgisMinimumVersion is set to less than  1.8 (%s) and there were errors reading metadata from the __init__.py file. This can lead to errors in versions of QGIS less than 1.8, please either set the qgisMinimumVersion to 1.8 or specify the metadata also in the __init__.py file. Reported error was: %s" % (min_qgs_version, ','.join(e.messages)))

    zip.close()
    del zip

    # Check author
    if 'author' in dict(metadata):
        if not re.match(r'^[^/]+$', dict(metadata)['author']):
           raise ValidationError("Author name cannot contain slashes.")

    # strip and check
    checked_metadata = []
    for k,v in metadata:
        try:
            if not (k in PLUGIN_BOOLEAN_METADATA or k == 'icon_content'):
                #v.decode('UTF-8')
                checked_metadata.append((k, v.strip()))
            else:
                checked_metadata.append((k, v))
        except UnicodeDecodeError, e:
            raise ValidationError("There was an error converting metadata '%s' to UTF-8 . Reported error was: %s" % (k, e))
    return checked_metadata
