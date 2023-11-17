{
  python3Packages,
  callPackage,
  extraPythonPackages ? [],
  bannerDir ? null,
}:
let 
  issStatic = (callPackage ./src/statics {});
in
python3Packages.buildPythonPackage {
  name = "ISS";
  src = ./.;
  format = "pyproject";

  nativeBuildInputs = with python3Packages; [
    build
    setuptools
    issStatic
  ];

  propagatedBuildInputs = with python3Packages; [
    django
    pytz
    pillow
    psycopg2
    lxml
    requests
    (pkgs.callPackage ./nix-deps/django-recaptcha2 {})
    (pkgs.callPackage ./nix-deps/email-normalize {})
    (pkgs.callPackage ./nix-deps/bbcode {})
    (pkgs.callPackage ./nix-deps/tripphrase {})
  ] ++ extraPythonPackages;

  preBuild = ''
    declare BANNER_DIR="${if isNull bannerDir then "" else bannerDir}"
    if [ -n "$BANNER_DIR" ]; then
      mkdir -p ./src/ISS/static/banners
      cp -r $BANNER_DIR/* ./src/ISS/static/banners
    fi
    cp -r --remove-destination ${issStatic}/lib/node_modules/iss-static/dist/* ./src/ISS/static
  '';
}
