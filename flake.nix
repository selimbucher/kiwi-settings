{
  description = "Kiwi Settings";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  outputs = { self, nixpkgs }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};

    kiwi-settings = pkgs.python3Packages.buildPythonApplication {
      pname = "kiwi-settings";
      version = "0.1.0";
      src = ./.;

      format = "other";

      nativeBuildInputs = with pkgs; [
        wrapGAppsHook4
        gobject-introspection
      ];

      buildInputs = with pkgs; [
        gtk4
        libadwaita
        glib
      ];

      propagatedBuildInputs = with pkgs.python3Packages; [
        pygobject3
      ];

      installPhase = ''
        mkdir -p $out/bin $out/lib/kiwi-settings $out/share/applications

        cp -r src/. $out/lib/kiwi-settings/

        makeWrapper ${pkgs.python3.withPackages (ps: [ ps.pygobject3 ])}/bin/python3 $out/bin/kiwi-settings \
          --add-flags "$out/lib/kiwi-settings/main.py" \
          --set PYTHONPATH "$out/lib/kiwi-settings" \
          --prefix PATH : ${pkgs.imagemagick}/bin

        cp data/kiwi-settings.desktop $out/share/applications/kiwi-settings.desktop
      '';
    };
  in {
    packages.${system}.default = kiwi-settings;

    devShells.${system}.default = pkgs.mkShell {
      buildInputs = with pkgs; [
        gtk4
        libadwaita
        gobject-introspection
        (python3.withPackages (ps: [ ps.pygobject3 ]))
      ];
    };
  };
}