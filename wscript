#!/usr/bin/evn python
# encoding: utf-8
# Copyright (C) 2012-2016 Michael Fisher <mfisher@kushview.net>

''' This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public Licence as published by
the Free Software Foundation, either version 2 of the Licence, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
file COPYING for more details. '''

import sys, os, platform
from subprocess import call
from waflib.extras import juce as juce
from waflib.extras import autowaf as autowaf

JUCE_VERSION = '5.4.3'
JUCE_MAJOR_VERSION = JUCE_VERSION[0]
JUCE_MINOR_VERSION = JUCE_VERSION[2]
JUCE_MICRO_VERSION = JUCE_VERSION[4]
JUCE_EXTRA_VERSION = ''

APPNAME = 'libjuce'
VERSION = JUCE_VERSION

top = '.'
out = 'build'

library_modules = '''
    juce_analytics
    juce_audio_basics
    juce_audio_devices
    juce_audio_formats
    juce_audio_processors
    juce_audio_utils
    juce_blocks_basics
    juce_box2d
    juce_core
    juce_cryptography
    juce_data_structures
    juce_events
    juce_opengl
    juce_osc
    juce_graphics
    juce_gui_basics
    juce_gui_extra
    juce_product_unlocking
    juce_video
'''.split()

cpponly_modules = '''
    juce_analytics
    juce_osc 
    juce_box2d
    juce_blocks_basics
'''.split()

mingw32_libs = '''
    gdi32 uuid wsock32 wininet version ole32 ws2_32 oleaut32 imm32 \
    comdlg32 shlwapi rpcrt4 winmm opengl32
'''

def options (opts):
    autowaf.set_options (opts)
    opts.load ('compiler_c compiler_cxx juce autowaf')
    opts.add_option('--projucer', default=False, action="store_true", \
        dest="projucer", help="Build the Projucer [ Default: False ]")
    opts.add_option('--juce-demo', default=False, action="store_true", \
        dest="juce_demo", help="Build the JUCE Demo [ Default: False ]")
    opts.add_option('--no-headers', default=True, action="store_false", \
        dest="install_headers", help="Don't install headers")
    opts.add_option('--disable-multi', default=True, action="store_false", \
        dest="enable_multi", help="Compile individual modules as libraries")
    opts.add_option('--static', default=False, action="store_true", \
        dest="static", help="Build Static Libraries [ Default: False ]")
    
    opts.add_option('--ziptype', default='gz', type='string', \
        dest='ziptype', help="Zip type for waf dist (gz/bz2/zip) [ Default: gz ]")
    
    group = opts.add_option_group ("Analytics")
    group.add_option('--exclude-analytics', default=True, action="store_false", \
        dest="juce_analytics", help="Don't build JUCE Analytics module")
    
    group = opts.add_option_group ("Graphics")
    group.add_option('--system-jpeg', default=False, action="store_true", \
        dest="system_jpeg", help="Use system JPEG")
    group.add_option('--system-png', default=False, action="store_true", \
        dest="system_png", help="Use system PNG")
    
    group = opts.add_option_group ("Audio Devices")
    group.add_option('--disable-alsa', default=True, action="store_false", \
        dest="alsa", help="Disable ALSA support")
    group.add_option('--enable-jack', default=False, action="store_true", \
        dest="jack", help="Enable JACK audio")

    group = opts.add_option_group ("Audio Processors")
    group.add_option('--enable-vst', default=False, action="store_true", \
        dest="vst", help="Enable VST hosting support [ Default: disabled ]")
    group.add_option('--enable-vst3', default=False, action="store_true", \
        dest="vst3", help="Enable VST3 hosting support [ Default: disabled ]")
    group.add_option('--enable-audio-unit', default=False, action="store_true", \
        dest="audio_unit", help="Enable Audio Unit hosting support [ Default: disabled ]")
    group.add_option('--enable-ladspa', default=False, action="store_true", \
        dest="ladspa", help="Enable LADSPA hosting support [ Default: disabled ]")

def configure (conf):
    conf.prefer_clang()
    conf.load ('compiler_c compiler_cxx autowaf')
    
    conf.env.DEBUG              = conf.options.debug
    conf.env.BUILD_DOCS         = conf.options.docs
    conf.env.BUILD_PROJUCER     = conf.options.projucer
    conf.env.BUILD_JUCE_DEMO    = conf.options.juce_demo
    conf.env.BUILD_MULTI        = conf.options.enable_multi
    conf.env.BUILD_STATIC       = conf.options.static
    conf.env.INSTALL_HEADERS    = conf.options.install_headers

    conf.env.VST3               = conf.options.vst3
    conf.env.VST                = conf.options.vst
    conf.env.LADSPA             = conf.options.ladspa
    conf.env.AUDIO_UNIT         = conf.options.audio_unit

    conf.env.DATADIR            = conf.env.PREFIX + '/share'
    conf.env.LIBDIR             = conf.env.PREFIX + '/lib'
    conf.env.BINDIR             = conf.env.PREFIX + '/bin'
    conf.env.INCLUDEDIR         = conf.env.PREFIX + '/include'

    conf.env.MODULES    = library_modules
    if not conf.options.juce_analytics:
        conf.env.MODULES.remove ('juce_analytics')
    
    # Write out the version header
    conf.define ("JUCE_VERSION", JUCE_VERSION)
    conf.define ("JUCE_MAJOR_VERSION", JUCE_MAJOR_VERSION)
    conf.define ("JUCE_MINOR_VERSION", JUCE_MINOR_VERSION)
    conf.define ("JUCE_MICRO_VERSION", JUCE_MICRO_VERSION)
    conf.define ("JUCE_EXTRA_VERSION", JUCE_EXTRA_VERSION)
    conf.write_config_header ('juce/version.h', 'LIBJUCE_VERSION_H')

    conf.check_cxx_version()
    conf.check_inline()
    
    cross_mingw = 'mingw32' in conf.env.CXX[0]
    if juce.is_mac():
        pass

    elif not cross_mingw and juce.is_linux():
        conf.check (header_name='pthread.h', uselib_store='PTHREAD', mandatory=True)
        conf.check (lib='pthread', uselib_store='PTHREAD', mandatory=True)

        if conf.options.system_png:
            conf.check_cfg (package='libpng', uselib_store='PNG', args=['--libs', '--cflags'], mandatory=True)

        if conf.options.system_jpeg:
            conf.check (header_name='stdio.h', uselib_store='STDIO', mandatory=True, auto_add_header_name=True)
            conf.check (header_name='jpegint.h', uselib_store='JPEG', mandatory=True, auto_add_header_name=True)
            conf.check (header_name='jpeglib.h', uselib_store='JPEG', mandatory=True)
            conf.check (lib='jpeg', uselib_store='JPEG', mandatory=True)
        
        conf.check (header_name='ladspa.h', uselib_store='LADSPA', 
                    mandatory=conf.options.ladspa)

        conf.check_cfg (package='freetype2', uselib_store='FREETYPE2', args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='libcurl', uselib_store='CURL', args=['--libs', '--cflags'], mandatory=False)
        conf.check_cfg (package='x11',  uselib_store='X11',  args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='xext', uselib_store='XEXT', args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='xinerama', uselib_store='XINERAMA', args=['--libs', '--cflags'], mandatory=False)
        conf.check_cfg (package='xrandr', uselib_store='XRANDR', args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='xcursor', uselib_store='XCURSOR', args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='gl', uselib_store='GL', args=['--libs', '--cflags'], mandatory=False)
        conf.check_cfg (package='gtk+-3.0',   uselib_store='GTK',   args=['--libs', '--cflags'], mandatory=False)
        conf.check_cfg (package='webkit2gtk-4.0',   uselib_store='WEBKIT',   args=['--libs', '--cflags'], mandatory=False)
        
        conf.check_cfg (package='alsa', uselib_store='ALSA', args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='jack', uselib_store='JACK', args=['--libs', '--cflags'], mandatory=False)

    elif cross_mingw or juce.is_windows():
        for l in mingw32_libs.split():
            conf.check (lib=l, uselib_store=l.upper(), mandatory=True)

    conf.write_config_header ("libjuce_config.h")

    conf.env.ALSA = conf.options.alsa and bool(conf.env.HAVE_ALSA)
    conf.env.JACK = conf.options.jack and bool(conf.env.HAVE_JACK)

    # Write juce/config.h
    conf.define ('JUCE_REPORT_APP_USAGE', 0)
    conf.define ('JUCE_DISPLAY_SPLASH_SCREEN', 0)
    conf.define ('JUCE_USE_DARK_SPLASH_SCREEN', 0)

    conf.define ('JUCE_USE_CURL', bool(conf.env.HAVE_CURL))
    
    conf.define ('JUCE_INCLUDE_PNGLIB_CODE', not bool(conf.env.LIB_PNG))
    conf.define ('JUCE_INCLUDE_JPEGLIB_CODE', not bool(conf.env.LIB_JPEG))

    if juce.is_linux():
        conf.env.WEB_BROWSER = bool(conf.env.HAVE_GTK) and bool(conf.env.HAVE_WEBKIT)
    else:
        conf.env.WEB_BROWSER = True
    conf.define ('JUCE_WEB_BROWSER', conf.env.WEB_BROWSER)

    conf.define ('JUCE_ALSA', conf.env.ALSA)
    conf.define ('JUCE_JACK', conf.env.JACK)
    conf.define ('JUCE_WASAPI', 0)
    conf.define ('JUCE_DIRECTSOUND', 0)
    conf.define ('JUCE_WASAPI_EXCLUSIVE', 0)
    
    conf.define ('JUCE_PLUGINHOST_AU', conf.options.audio_unit)
    conf.define ('JUCE_PLUGINHOST_VST', conf.options.vst)
    conf.define ('JUCE_PLUGINHOST_VST3', conf.options.vst3)
    conf.define ('JUCE_PLUGINHOST_LADSPA', conf.options.ladspa and bool(conf.env.HAVE_LADSPA))

    conf.define ('JUCE_STANDALONE_APPLICATION', 0)
    
    for mod in library_modules:
        conf.define('JUCE_MODULE_AVAILABLE_%s' % mod, True)
    conf.write_config_header ('juce/config.h', 'LIBJUCE_MODULES_CONFIG_H')

    conf.load ('juce')
    conf.define ('JUCE_APP_CONFIG_HEADER', "juce/config.h")

    conf.env.JUCE_MODULE_PATH = 'src/modules'
    conf.env.append_unique ('CXXFLAGS', '-I' + os.getcwd() + '/build')
    conf.env.append_unique ('CFLAGS', '-I' + os.getcwd() + '/build')

    print
    juce.display_header ('libJUCE')
    juce.display_msg (conf, 'Version', VERSION)
    juce.display_msg (conf, 'Prefix', conf.env.PREFIX)
    juce.display_msg (conf, 'Debuggable', conf.env.DEBUG)

    print
    juce.display_header ('Modules')
    for m in library_modules:
        juce.display_msg (conf, m.replace('juce_', ''), m in conf.env.MODULES)

    print
    juce.display_header ('Core')
    juce.display_msg (conf, 'CURL', bool(conf.env.LIB_CURL))

    print
    juce.display_header ('Audio Devices')
    juce.display_msg (conf, 'JACK', conf.env.JACK)
    juce.display_msg (conf, 'ALSA', conf.env.ALSA)

    print
    juce.display_header ('Graphics')
    juce.display_msg (conf, 'System PNG', bool(conf.env.LIB_PNG))
    juce.display_msg (conf, 'System JPEG', bool(conf.env.LIB_JPEG))
    
    print
    juce.display_header ('GUI Extra')
    juce.display_msg (conf, 'Web Browser', conf.env.WEB_BROWSER)

    print
    juce.display_header ('Plugin Host')
    juce.display_msg (conf, 'AudioUnit',    conf.env.AUDIO_UNIT)
    juce.display_msg (conf, 'VST',          conf.env.VST)
    juce.display_msg (conf, 'VST3',         conf.env.VST3)
    juce.display_msg (conf, 'LADSPA',       conf.env.LADSPA)

    print
    juce.display_header ('Applications')
    juce.display_msg (conf, 'Projucer', bool (conf.env.BUILD_PROJUCER))

    if juce.is_mac():
        print
        juce.display_header ('Mac Options')
        juce.display_msg (conf, 'OSX Arch', conf.env.ARCH)
        juce.display_msg (conf, 'OSX Min Version', conf.options.mac_version_min)
        juce.display_msg (conf, 'OSX SDK', conf.options.mac_sdk)
    
    print
    juce.display_header ('Global Compiler Flags')
    juce.display_msg (conf, 'CFLAGS', conf.env.CFLAGS)
    juce.display_msg (conf, 'CXXFLAGS', conf.env.CXXFLAGS)
    juce.display_msg (conf, 'LDFLAGS', conf.env.LINKFLAGS)

def get_include_path (bld, subpath=''):
    ip = '%s/juce-%s' % (bld.env.INCLUDEDIR, JUCE_MAJOR_VERSION)
    ip = os.path.join (ip, subpath) if len(subpath) > 0 else ip
    return ip

def install_module_headers (bld, modules):
    for mod in modules:
        bld.install_files (get_include_path (bld), \
                           bld.path.ant_glob ("src/modules/" + mod + "/**/*.h"), \
                           relative_trick=True, cwd=bld.path.find_dir ('src/modules'))

def install_misc_header (bld, header, subpath=''):
    destination = get_include_path (bld, subpath)
    bld.install_files (destination, header)

def maybe_install_headers (bld):
    if not bld.env.INSTALL_HEADERS:
        return
    
    install_module_headers (bld, library_modules)

    for header in ['juce/juce.h' ]:
        install_misc_header (bld, header, 'juce')

    for mod in library_modules:
        install_misc_header (bld, "build/juce/%s.h" % mod.replace ('juce_', ''), 'juce')

    install_misc_header (bld, 'build/juce/config.h', 'juce')
    install_misc_header (bld, 'build/juce/version.h', 'juce')

def module_slug (ctx, mod):
    debug = ctx.env.DEBUG
    slug = mod
    if debug: slug += '_debug'
    slug += '-%s' % JUCE_MAJOR_VERSION
    return slug

def library_slug (ctx, name):
    mv = JUCE_MAJOR_VERSION
    debug = ctx.env.DEBUG
    slug = name + '_debug-%s' % mv if debug else name + '-%s' % mv
    return slug

def build_osx (bld):
    source = [ ]
    for mod in library_modules:
        extension = 'mm'
        if mod in cpponly_modules:
            extension = 'cpp'
        file = 'build/code/include_%s.%s' % (mod, extension)
        source.append (file)
    source.append ('project/dummy.cpp')

    library = bld.shlib (
        source      = source,
        includes    = [ 'juce', 'src/modules' ],
        name        = 'JUCE',
        target      = 'local/lib/%s' % library_slug (bld, 'juce'),
        use         = [ 'AUDIO_TOOLBOX', 'COCOA', 'CORE_AUDIO', 'CORE_MIDI', 'OPEN_GL', \
                        'ACCELERATE', 'IO_KIT', 'QUARTZ_CORE', 'WEB_KIT', 'CORE_MEDIA',
                        'AV_FOUNDATION', 'AV_KIT' ],
        env         = bld.env.derive(),
        vnum        = JUCE_VERSION
    )
    
    if bld.env.AUDIO_UNIT: library.use.append ('CORE_AUDIO_KIT')

    pcobj = bld (
        features      = 'subst',
        source        = 'juce.pc.in',
        target        = '%s.pc' % library_slug (bld, 'juce'),
        install_path  = os.path.join (bld.env.LIBDIR, 'pkgconfig'),
        MAJOR_VERSION = JUCE_MAJOR_VERSION,
        PREFIX        = bld.env.PREFIX,
        INCLUDEDIR    = bld.env.INCLUDEDIR,
        LIBDIR        = bld.env.LIBDIR,
        CFLAGS        = '',
        DEPLIBS       = '-l%s' % library_slug (bld, 'juce'),
        REQUIRED      = '',
        NAME          = 'JUCE',
        DESCRIPTION   = 'JUCE library modules',
        VERSION       = JUCE_VERSION
    )

    if not bld.env.DEBUG:
        pcobj.CFLAGS += ' -DNDEBUG=1'
    else:
        pcobj.CFLAGS += ' -DDEBUG=1'

def build_cross_mingw (bld):
    '''Not yet supported'''
    return

def build_modules (bld):
    subst_env = bld.env.derive()
    subst_env.CFLAGS = []

    for m in bld.env.MODULES:
        module = juce.get_module_info (bld, m)
        slug = module_slug (bld, m)
        
        ext = 'mm' if juce.is_mac() else 'cpp'
        if ext == 'mm' and not os.path.exists ('src/modules/%s/%s.mm' % (m, m)):
            ext = 'cpp'

        module_libname = '%s' % (module_slug (bld, m))

        library = bld (
            features    = 'cxxshlib cxx',
            includes    = [ 'juce', 'src/modules' ],
            source      = [ 'build/code/include_%s.%s' % (m, ext) ],
            target      = 'local/lib/%s' % module_libname,
            name        = m.upper(),
            use         = [u.upper() for u in module.dependencies()],
            vnum        = module.version()
        )
        
        if bld.env.VST3:
            library.includes.append ('src/modules/juce_audio_processors/format_types/VST3_SDK')
        
        if juce.is_linux():
            library.use += module.linuxPackages()
            if m == 'juce_gui_extra':
                if bool(bld.env.HAVE_WEBKIT):
                    library.use.append('WEBKIT')

        if juce.is_mac():
            library.use += module.osxFrameworks()
            if m == 'juce_product_unlocking':
                for e in 'juce_gui_extra juce_data_structures'.split():
                    if e in library_modules:
                        library.use.append (e.upper())
            elif m == 'juce_audio_processors':
                if bld.env.AUDIO_UNIT:
                    library.use.append ('CORE_AUDIO_KIT')

        # Pkg Config Files
        pcobj = bld (
            features     = 'subst',
            source       = 'juce_module.pc.in',
            target       = slug + '.pc',
            install_path = bld.env.LIBDIR + '/pkgconfig',
            env          = subst_env,
            MAJOR_VERSION= JUCE_MAJOR_VERSION,
            PREFIX       = bld.env.PREFIX,
            INCLUDEDIR   = bld.env.INCLUDEDIR,
            LIBDIR       = bld.env.LIBDIR,
            CFLAGS       = '',
            DEPLIBS      = '-l%s' % module_libname,
            REQUIRED     = ' '.join (module.requiredPackages (bool (bld.env.DEBUG))),
            NAME         = module.name(),
            DESCRIPTION  = module.description(),
            VERSION      = module.version(),
        )

        if not bld.env.DEBUG:
            pcobj.CFLAGS += ' -DNDEBUG=1'
        else:
            pcobj.CFLAGS += ' -DDEBUG=1'

        if juce.is_mac():
            for framework in module.osxFrameworks (False):
                pcobj.DEPLIBS += ' -framework %s' % framework
    
    jpcobj = bld (
        features     = 'subst',
        source       = 'juce.pc.in',
        target       = library_slug (bld, 'juce') + '.pc',
        install_path = bld.env.LIBDIR + '/pkgconfig',
        env          = subst_env,
        MAJOR_VERSION= JUCE_MAJOR_VERSION,
        PREFIX       = bld.env.PREFIX,
        INCLUDEDIR   = bld.env.INCLUDEDIR,
        LIBDIR       = bld.env.LIBDIR,
        CFLAGS       = None,
        DEPLIBS      = '',
        REQUIRED     = '',
        NAME         = 'JUCE',
        DESCRIPTION  = 'JUCE',
        VERSION      = VERSION,
    )
    required = []
    for mod in bld.env.MODULES:
        required.append (module_slug (bld, mod))

    jpcobj.REQUIRED = ' '.join (required)

    maybe_install_headers (bld)

def build_single (bld):
    if juce.is_mac():
        build_osx (bld)

def generate_code (bld):
    for mod in library_modules:
        bld (
            features     = 'subst',
            source       = 'module_header.h.in',
            target       = 'juce/%s.h' % mod.replace ('juce_', ''),
            name         = mod + "_h",
            install_path = None,
            MODULE       = mod
        )

        bld (
            features     = 'subst',
            source       = 'module_code.cpp.in',
            target       = 'code/include_%s.cpp' % mod,
            name         = mod + "_cpp",
            install_path = None,
            MODULE       = mod
        )

        if not mod in cpponly_modules:
            bld (
                features     = 'subst',
                source       = 'module_code.mm.in',
                target       = 'code/include_%s.mm' % mod,
                name         = mod + "_mm",
                install_path = None,
                MODULE       = mod
            )
    bld.add_group()

def build (bld):
    bld.env.INSTALL_HEADERS = bld.options.install_headers
    
    generate_code (bld)

    if bld.env.BUILD_MULTI:
        build_modules (bld)
    else:
        build_single (bld)

    def build_project (path, name):
        proj = juce.Project (bld, path)
        app = bld (
            features    = 'cxx cxxprogram',
            source      = proj.getProjectCode(),
            includes    = [ '.', 'juce', 'src/modules', 'juce/compat/%s/Source' % name ],
            name        = name,
            target      = name,
            use         = [u.upper() for u in proj.getModules()]
        )
        bd = os.path.join (proj.getLibraryCodePath(), 'BinaryData.cpp')
        if os.path.exists (bd):
            app.source.append (bd)
        
        if juce.is_mac():
            app.mac_app         = True
            app.mac_plist       = 'juce/compat/%s/Info-App.plist' % name
            app.mac_files       = [ 'src/extras/%s/Builds/MacOSX/RecentFilesMenuTemplate.nib' % name,
                                    'src/extras/%s/Builds/MacOSX/Icon.icns' % name ]
            app.target          = 'Applications/%s' % name

        return app

    if bld.env.BUILD_PROJUCER:
        build_project ('src/extras/Projucer/Projucer.jucer', 'Projucer')
        if juce.is_mac():
            bld.add_post_fun(macdeploy)
    
    maybe_install_headers (bld)

    if bld.env.BUILD_DOCS:
        if not bld.is_install:
            bld.add_post_fun(build_docs)
        bld.install_files (bld.env.DOCDIR, \
                           bld.path.ant_glob ("build/doc/**/*"), \
                           relative_trick=True, cwd=bld.path.find_dir ('build/doc'))

def build_docs(ctx):
    call(['bash', 'tools/build-docs.sh'])

def dist (ctx):
    z = ctx.options.ziptype
    if 'zip' in z:
        ziptype = z
    else:
        ziptype = "tar." + z

    ctx.algo = ziptype
    ctx.base_name = '%s-%s' % (APPNAME, VERSION)
    ctx.excl = ' **/.waf-1* **/.waf-2* **/*~ **/*.pyc **/*.swp **/.lock-w*'
    ctx.excl += ' **/.gitignore **/.gitmodules **/.git dist build **/.DS_Store'
    ctx.excl += ' project/Builds **/.vscode'

def macdeploy (ctx):
    call (["tools/appbundle.py", "-verbose", "2",
            "build/Applications/Projucer.app"])
