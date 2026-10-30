{ lib
, stdenv
, python3
, gtk3
, gtk-layer-shell
, gobject-introspection
, wrapGAppsHook3
}:

let
  pythonEnv = python3.withPackages (ps: [
    ps.pygobject3
    ps.evdev
  ]);
in
stdenv.mkDerivation {
  pname = "wayland-scrollbar";
  version = "1.0.0";
  src = ./.;

  nativeBuildInputs = [
    gobject-introspection
    wrapGAppsHook3
  ];

  buildInputs = [
    gtk3
    gtk-layer-shell
    pythonEnv
  ];

  dontBuild = true;

  installPhase = ''
    mkdir -p $out/bin $out/lib/wayland-scrollbar
    cp wayland_scrollbar.py $out/lib/wayland-scrollbar/
    chmod +x $out/lib/wayland-scrollbar/wayland_scrollbar.py

    makeWrapper ${pythonEnv}/bin/python3 $out/bin/wayland-scrollbar \
      --add-flags "$out/lib/wayland-scrollbar/wayland_scrollbar.py" \
      --prefix GI_TYPELIB_PATH : "${gtk3}/lib/girepository-1.0:${gtk-layer-shell}/lib/girepository-1.0" \
      --prefix LD_LIBRARY_PATH : "${gtk-layer-shell}/lib"

    # Compatibility symlink
    ln -s $out/bin/wayland-scrollbar $out/bin/niri-scrollbar
  '';

  meta = with lib; {
    description = "Invisible gesture & IPC scrollbar for scrolling Wayland compositors (Niri, Umbriel)";
    license = licenses.mit;
    platforms = platforms.linux;
    mainProgram = "wayland-scrollbar";
  };
}
