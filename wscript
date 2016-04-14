#!/usr/bin/evn python
# encoding: utf-8
# Copyright (C) 2012 Michael Fisher <mfisher31@gmail.com>

''' This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public Licence as published by
the Free Software Foundation, either version 3 of the Licence, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
file COPYING for more details. '''

import sys, os, platform
from subprocess import call

sys.path.insert(0, "tools/waf")
import juce
from juce import IntrojucerProject as Project
from juce import ModuleInfo as ModuleInfo

JUCE_VERSION = '4.2.0'
JUCE_MAJOR_VERSION = JUCE_VERSION[0]
JUCE_MINOR_VERSION = JUCE_VERSION[2]
JUCE_MICRO_VERSION = JUCE_VERSION[4]
JUCE_EXTRA_VERSION = ''

# For waf dist
APPNAME = 'libjuce'
VERSION = JUCE_VERSION

# Waf wants these as well
top = '.'
out = 'build'

library_modules = '''
    juce_audio_basics
    juce_audio_devices
    juce_audio_formats
    juce_audio_processors
    juce_audio_utils
    juce_box2d
    juce_core
    juce_cryptography
    juce_data_structures
    juce_events
    juce_opengl
    juce_graphics
    juce_gui_basics
    juce_gui_extra
    juce_osc
    juce_tracktion_marketplace
    juce_video
'''.split()

mingw32_libs = 'gdi32 uuid wsock32 wininet version ole32 ws2_32 oleaut32 imm32 comdlg32 shlwapi rpcrt4 winmm opengl32'

def options(opts):
    opts.load ('compiler_c compiler_cxx juce')

    opts.add_option('--introjucer', default=False, action="store_true", \
        dest="introjucer", help="Build the Introjucer [ Default: False ]")
    opts.add_option('--juce-demo', default=False, action="store_true", \
        dest="juce_demo", help="Build the JUCE Demo [ Default: False ]")
    opts.add_option('--no-headers', default=True, action="store_false", \
        dest="install_headers", help="Don't install headers")
    opts.add_option('--no-juce-libs', default=True, action="store_false", \
        dest="no_juce_libs", help="Don't compile modules as shared libraries")
    opts.add_option('--static', default=False, action="store_true", \
        dest="static", help="Build Static Libraries [ Default: False ]")
    opts.add_option('--ziptype', default='gz', type='string', \
        dest='ziptype', help="Zip type for waf dist (gz/bz2/zip) [ Default: gz ]")
    opts.add_option('--system-jpeg', default=False, action="store_true", \
        dest="system_jpeg", help="Use system JPEG")
    opts.add_option('--system-png', default=False, action="store_true", \
        dest="system_png", help="Use system PNG")

def configure (conf):
    conf.prefer_clang()
    conf.load ('compiler_c compiler_cxx')

    # Store options in environment
    conf.env.BUILD_DEBUGGABLE   = conf.options.debug
    conf.env.BUILD_INTROJUCER   = conf.options.introjucer
    conf.env.BUILD_JUCE_DEMO    = conf.options.juce_demo
    conf.env.BUILD_JUCE_MODULES = conf.options.no_juce_libs
    conf.env.BUILD_STATIC       = conf.options.static
    conf.env.INSTALL_HEADERS    = conf.options.install_headers

    conf.env.DATADIR    = conf.env.PREFIX + '/share'
    conf.env.LIBDIR     = conf.env.PREFIX + '/lib'
    conf.env.BINDIR     = conf.env.PREFIX + '/bin'
    conf.env.INCLUDEDIR = conf.env.PREFIX + '/include'

    # Write out the version header
    conf.define ("JUCE_VERSION", JUCE_VERSION)
    conf.define ("JUCE_MAJOR_VERSION", JUCE_MAJOR_VERSION)
    conf.define ("JUCE_MINOR_VERSION", JUCE_MINOR_VERSION)
    conf.define ("JUCE_MICRO_VERSION", JUCE_MICRO_VERSION)
    conf.define ("JUCE_EXTRA_VERSION", JUCE_EXTRA_VERSION)
    conf.write_config_header ('modules/version.h', 'LIBJUCE_VERSION_H')

    conf.check_cxx11()
    conf.check_inline()

    cross_mingw = 'mingw32' in conf.env.CXX[0]
    if juce.is_mac():
        pass

    elif not cross_mingw and juce.is_linux():
        if conf.options.system_png:
            conf.check_cfg (package='libpng', uselib_store='PNG', args=['--libs', '--cflags'], mandatory=True)

        if conf.options.system_jpeg:
            conf.check (header_name='stdio.h', uselib_store='STDIO', mandatory=True, auto_add_header_name=True)
            conf.check (header_name='jpegint.h', uselib_store='JPEG', mandatory=True, auto_add_header_name=True)
            conf.check (header_name='jpeglib.h', uselib_store='JPEG', mandatory=True)
            conf.check (lib='jpeg', uselib_store='JPEG', mandatory=True)

        conf.check_cfg (package='freetype2', uselib_store='FREETYPE', args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='libcurl', uselib_store='CURL', args=['--libs', '--cflags'], mandatory=False)
        conf.check_cfg (package='x11',  uselib_store='X11',  args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='xext', uselib_store='XEXT', args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='gl',   uselib_store='GL',   args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='alsa', uselib_store='ALSA', args=['--libs', '--cflags'], mandatory=True)
        conf.check_cfg (package='jack', uselib_store='JACK', args=['--libs', '--cflags'], mandatory=False)

    elif cross_mingw or juce.is_windows():
        for l in mingw32_libs.split():
            conf.check (lib=l, uselib_store=l.upper(), mandatory=True)

    conf.write_config_header ("libjuce_config.h")

    # Write modules/config.h "
    conf.define ('JUCE_USE_CURL', len(conf.env.LIB_CURL) > 0)
    conf.define ('JUCE_USE_ALSA', len(conf.env.LIB_ALSA) > 0)
    conf.define ('JUCE_USE_JACK', len(conf.env.LIB_JACK) > 0)
    conf.define ('JUCE_INCLUDE_PNGLIB_CODE', len(conf.env.LIB_PNG) <= 0)
    conf.define ('JUCE_INCLUDE_JPEGLIB_CODE', len(conf.env.LIB_JPEG) <= 0)

    conf.define ('JUCE_WASAPI', False)
    conf.define ('JUCE_DIRECTSOUND', False)
    conf.define ('JUCE_WASAPI_EXCLUSIVE', False)

    conf.define ('JUCE_STANDALONE_APPLICATION', 0)
    for mod in library_modules:
        conf.define('JUCE_MODULE_AVAILABLE_%s' % mod, True)
    conf.write_config_header ('modules/config.h', 'LIBJUCE_MODULES_CONFIG_H')

    # conf.define('JUCE_APP_CONFIG_HEADER', 'modules/config.h')
    conf.env.JUCE_MODULE_PATH = 'src/modules'
    conf.load('juce')
    conf.env.append_unique ('CXXFLAGS', '-I' + os.getcwd() + '/build')
    conf.env.append_unique ('CFLAGS', '-I' + os.getcwd() + '/build')

    print
    juce.display_header ('libJUCE Configuration')
    juce.display_msg (conf, 'JUCE Library Version', VERSION)
    juce.display_msg (conf, 'Prefix', conf.env.PREFIX)
    juce.display_msg (conf, 'Install Headers', conf.env.INSTALL_HEADERS)
    juce.display_msg (conf, 'Build Debuggable Libraries', conf.env.BUILD_DEBUGGABLE)
    juce.display_msg (conf, 'Build Introjucer', conf.env.BUILD_INTROJUCER)
    juce.display_msg (conf, 'Build Juce Demo', conf.env.BUILD_JUCE_DEMO)
    juce.display_msg (conf, 'Build Modules', conf.env.BUILD_JUCE_MODULES)
    juce.display_msg (conf, 'Build Static Libraries', conf.env.BUILD_STATIC)
    print
    juce.display_header ('Global Compiler Flags')
    juce.display_msg (conf, 'CFLAGS', conf.env.CFLAGS)
    juce.display_msg (conf, 'CXXFLAGS', conf.env.CXXFLAGS)
    juce.display_msg (conf, 'LDFLAGS', conf.env.LINKFLAGS)

def make_desktop (bld, slug):
    if not juce.is_linux():
        return

    location = 'data'
    src = "data/%s.desktop.in" % (slug)
    tgt = "%s.desktop" % (slug)

    if os.path.exists (src):
        bld (features = "subst",
             source    = src,
             target    = tgt,
             name      = tgt,
             JUCE_BIN  = bld.env.BINDIR,
             JUCE_DATA = "%s/juce" % (bld.env.DATADIR),
             install_path = bld.env.DATADIR + "/applications"
        )

def get_include_path(bld):
    return bld.env.INCLUDEDIR + '/juce-%s/juce' % JUCE_MAJOR_VERSION

def install_module_headers (bld, modules):
    for mod in modules:
        bld.install_files (get_include_path (bld), \
                           bld.path.ant_glob ("src/modules/" + mod + "/**/*.h"), \
                           relative_trick=True, cwd=bld.path.find_dir ('src'))

def install_misc_header (bld, h, subpath=''):
    p = get_include_path(bld) + subpath
    bld.install_files (p, h)

def maybe_install_headers(bld):
    if bld.env.INSTALL_HEADERS:
        install_module_headers (bld, library_modules)
        for header in ['juce/juce.h', 'juce/AppConfig.h', 'juce/JuceHeader.h']:
            install_misc_header (bld, header)
        install_misc_header (bld, 'build/modules/config.h', '/modules')

def module_slug (mod, debug=False):
    slug = mod.replace('_', '-')
    if debug: slug += '-debug'
    slug += '-%s' % JUCE_MAJOR_VERSION
    return slug

def library_slug(mod, debug=False):
    mv = JUCE_MAJOR_VERSION
    slug = mod + '_debug-%s' % mv if debug else mod + '-%s' % mv
    return slug

def build_cross_mingw(bld):
    obj = juce.build_unified_library(bld, 'juce', library_modules)
    obj.name = 'libjuce'
    obj.vnum = JUCE_VERSION
    obj.includes += ['juce', 'src/modules']
    obj.use += mingw32_libs.upper().split()
    obj.cxxflags = ['-DJUCE_APP_CONFIG_HEADER="modules/config.h"']
    bld (
        features     = 'subst',
        source       = 'juce-module.pc.in',
        target       = 'juce.pc',
        install_path = bld.env.LIBDIR + '/pkgconfig',
        MAJOR_VERSION= JUCE_MAJOR_VERSION,
        PREFIX       = bld.env.PREFIX,
        INCLUDEDIR   = bld.env.INCLUDEDIR,
        LIBDIR       = bld.env.LIBDIR,
        DEPLIBS      = '-l%s-%s' % ('juce', JUCE_MAJOR_VERSION),
        REQUIRED     = '',
        NAME         = 'libJUCE',
        DESCRIPTION  = 'libJUCE',
        VERSION      = JUCE_VERSION,
    )

    maybe_install_headers (bld)

def build_modules(bld):
    if juce.is_linux() and 'w64-mingw' in bld.env.CXX[0]:
        return build_cross_mingw(bld)

    postfix = '_debug' if bld.env.BUILD_DEBUGGABLE else ''

    libs = juce.build_modular_libs (bld, library_modules, JUCE_VERSION, postfix)
    for lib in libs:
        lib.includes += ['juce', 'src/modules']
        lib.cxxflags = ['-DJUCE_APP_CONFIG_HEADER="modules/config.h"']

    # Create pkg-config files for all built modules
    is_debug = bld.env.BUILD_DEBUGGABLE
    for m in library_modules:
        module = juce.get_module_info (bld, m)
        slug = module_slug(m, is_debug)
        required_packages = ' '.join (module.requiredPackages (is_debug))
        deplibs = ' '.join (module.linuxLibs())

        if m == 'juce_core':
            for lib in bld.env.LIB_CURL:
                deplibs += ' -l%s' % lib

        deplibs += ' -l%s' % library_slug(m, is_debug)

        pcobj = bld (
            features     = 'subst',
            source       = 'juce-module.pc.in',
            target       = slug + '.pc',
            install_path = bld.env.LIBDIR + '/pkgconfig',
            MAJOR_VERSION= JUCE_MAJOR_VERSION,
            PREFIX       = bld.env.PREFIX,
            INCLUDEDIR   = bld.env.INCLUDEDIR,
            LIBDIR       = bld.env.LIBDIR,
            DEPLIBS      = deplibs,
            REQUIRED     = required_packages,
            NAME         = module.name(),
            DESCRIPTION  = module.description(),
            VERSION      = module.version(),
        )

    maybe_install_headers (bld)

def build_project (bld, project, name):
    is_mingw32 = juce.is_windows() or 'mingw' in bld.env.CXX[0]
    node = bld.path.find_resource (project)
    introjucer = juce.IntrojucerProject (bld, node.relpath())
    obj = introjucer.compile (bld)
    obj.cxxflags += ['-DJUCE_APP_CONFIG_HEADER="AppConfig.h"']
    obj.includes.append ('src/modules')
    obj.env = bld.env.derive()

    if juce.is_linux() and not is_mingw32:
        obj.use += ['GL', 'ALSA', 'FREETYPE', 'CURL', 'X11', 'XEXT']
        obj.linkflags = ['-lpthread', '-ldl']
        make_desktop (bld, name)
    elif is_mingw32:
        obj.use = mingw32_libs.upper().split()
        obj.linkflags = ''
    return obj

def build (bld):
    bld.env.INSTALL_HEADERS = bld.options.install_headers

    if bld.env.BUILD_JUCE_MODULES:
        build_modules(bld)

    # testing linkage against module libs
    is_mingw32 = juce.is_windows() or 'w64-mingw' in bld.env.CXX[0]
    disable_test_app = False
    if not disable_test_app:
        testapp = Project (bld, 'extras/TestApp/TestApp.jucer')
        if juce.is_linux() and not is_mingw32:
            juce_useflags = ['X11', 'XEXT', 'ALSA', 'GL', 'FREETYPE', 'CURL']
        elif juce.is_mac():
            juce_useflags = ['COCOA', 'IO_KIT']
        elif is_mingw32:
            juce_useflags = ['libjuce']

        obj = bld.program (
            source    = testapp.getProjectCode(),
            includes  = ['.', 'juce', 'src', 'src/modules'],
            name      = 'TestApp',
            target    = 'testapp',
            use       = juce_useflags,
            linkflags = '',
            install_path = None,
            cxxflags  = ['-DJUCE_GLOBAL_MODULE_SETTINGS_INCLUDED=1']
        )

        if juce.is_linux() and not is_mingw32:
            for mod in library_modules:
                pkgslug = module_slug(mod, bld.env.BUILD_DEBUGGABLE)
                juce_useflags.append (pkgslug)
            obj.linkflags = '-Wl,-rpath,$ORIGIN'
        elif juce.is_mac():
            obj.target  = 'Applications/TestApp'
            obj.mac_app = True
            obj.install_path = os.getcwd() + '/build/Applications' # workaround
        elif is_mingw32:
            pass

        bld.add_group()

    if bld.env.BUILD_INTROJUCER:
        build_project (bld, 'src/extras/Projucer/Projucer.jucer', 'Projucer')
    if bld.env.BUILD_JUCE_DEMO:
        build_project (bld, 'src/examples/Demo/JuceDemo.jucer', 'JuceDemo')

    if juce.is_linux() and (bld.env.BUILD_INTROJUCER or bld.env.BUILD_JUCE_DEMO):
        bld.install_files (bld.env.DATADIR + '/juce/icons', 'data/juce_icon.xpm')

def dist(ctx):
    z = ctx.options.ziptype
    if 'zip' in z:
        ziptype = z
    else:
        ziptype = "tar." + z
    ctx.algo = ziptype
