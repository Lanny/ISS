let 
  pkgs = import <nixpkgs> {};
  issStatic = (pkgs.callPackage ./src/ISS/static-src {});
in
pkgs.python3Packages.buildPythonPackage {
  name = "ISS";
  src = ./.;
  format = "pyproject";

  nativeBuildInputs = with pkgs.python3Packages; [
    build
    setuptools
    issStatic
  ];

  propagatedBuildInputs = with pkgs.python3Packages; [
    django
    django-redis
    pytz
    pillow
    psycopg2
    lxml
    requests
    django-debug-toolbar
    (pkgs.callPackage ./nix-deps/django-recaptcha2 {})
    (pkgs.callPackage ./nix-deps/email-normalize {})
    (pkgs.callPackage ./nix-deps/bbcode {})
    (pkgs.callPackage ./nix-deps/tripphrase {})
  ];

  preBuild = ''
    cp -r ${issStatic}/lib/node_modules/iss-static/dist/* ./src/ISS/static
  '';
}
