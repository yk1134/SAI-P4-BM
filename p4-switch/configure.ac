AC_INIT([p4-sai-bm], [0.1], [yonatanp@mellanox.com])

# check if the source folder is correct
AC_CONFIG_SRCDIR([sai-p4-target/simple_switch.cpp])

# Checks for programs

# check for C++ preprocessor and compiler and the library compiler
AC_PROG_CXXCPP
AC_PROG_CXX
AM_PROG_AR
LT_INIT

AM_PATH_PYTHON([2.7],, [:])

AC_CONFIG_MACRO_DIRS([m4])

# add this to ARG macro
P4_BM_DIR="behavioral-model"
AC_SUBST(P4_BM_DIR)

# Thrift
AC_PATH_PROG([THRIFT], [thrift], [])

# Create thrift output for sai_thrift_server (needed for ptf)
# echo "Generating thrift output file for sai_thrift_server"
# thrift --gen cpp --gen py -o sai_adapter/test/sai_thrift_src/ sai_adapter/test/sai_thrift_src/switch_sai.thrift 

# automake initialisation and check for minimal automake API version 1.9
AM_INIT_AUTOMAKE([-Wall -Werror foreign subdir-objects])

# use the C++ compiler for the following checks
AC_LANG([C++])

# Checks for header files.
AC_HEADER_STDC
AC_CHECK_HEADERS([string])
AC_CHECK_HEADERS([iostream])

# Checks for typedefs, structures, and compiler characteristics.
AC_TYPE_SIZE_T

# distribute additional compiler and linker flags
# --> set these variables instead of CXXFLAGS or LDFLAGS
AC_SUBST([AM_CXXFLAGS])
AC_SUBST([AM_CFLAGS])
AC_SUBST([AM_LDFLAGS])

# files to generate via autotools (.am or .in source files)
AC_CONFIG_FILES([Makefile])
AC_CONFIG_FILES([sai-p4-target/Makefile])

AC_ARG_WITH([targets],
    AS_HELP_STRING([--without-targets], [Do not build targets]),
    [], [want_targets=yes])

AM_CONDITIONAL([COND_TARGETS], [test "$want_targets" = yes])

AC_CONFIG_SUBDIRS([behavioral-model])

# generate the final Makefile etc.
AC_OUTPUT