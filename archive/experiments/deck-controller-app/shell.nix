{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python3
    python3Packages.pygame
    python3Packages.evdev
  ];

  shellHook = ''
    echo "Steam Deck Controller Forwarder Environment"
    echo "Python: $(python3 --version)"
    echo "Ready to run: python3 deck_controller_app.py"
  '';
}
