/* Shim for the CMake-generated DllMacro.h headers.
 *
 * When Calamares itself is built, each library gets a DllMacro.h
 * (libcalamares ships one in its source; libcalamaresui's is
 * CMake-generated) defining DLLEXPORT / UIDLLEXPORT. The OnionHost
 * view-module plugins are compiled against the installed Calamares
 * headers + libraries (not a full Calamares build), so this shim
 * provides both macros. On ELF platforms they resolve to default
 * visibility, which is what the generated headers produce there
 * too. The include guard intentionally matches the real headers:
 * whichever is seen first serves both libraries.
 */
#ifndef DLLMACRO_H
#define DLLMACRO_H

#ifndef DLLEXPORT
#define DLLEXPORT __attribute__( ( visibility( "default" ) ) )
#endif
#ifndef UIDLLEXPORT
#define UIDLLEXPORT __attribute__( ( visibility( "default" ) ) )
#endif

#endif  // DLLMACRO_H
