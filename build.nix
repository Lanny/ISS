let pkgs = import <nixpkgs> {}; in
pkgs.callPackage ./default.nix {
  extraPythonPackages = with pkgs.python3Packages; [
    django-debug-toolbar
    django-redis
  ];
  bannerDir = ./banners;
}

