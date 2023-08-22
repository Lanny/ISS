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
    (pkgs.callPackage ./django-recaptcha2 {})
    (pkgs.callPackage ./email-normalize {})
    (pkgs.callPackage ./bbcode {})
    (pkgs.callPackage ./tripphrase {})
  ];

  preBuild = ''
    rm -rf ./src/ISS/static
    cp -r ${issStatic}/lib/node_modules/iss-static/dist ./src/ISS/static
  '';
}
