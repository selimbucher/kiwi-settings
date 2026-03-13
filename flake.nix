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
        mkdir -p $out/bin
        cp main.py $out/bin/kiwi-settings
        chmod +x $out/bin/kiwi-settings
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