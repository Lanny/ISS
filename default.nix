let 
  pkgs = import <nixpkgs> {};
  issStatic = (pkgs.callPackage ./ISS/static-src {});
in
pkgs.stdenv.mkDerivation {
  name = "ISS";
  src = ./.;

  buildInputs = [
    (pkgs.python3.withPackages( ps: with ps; [
      django
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
    ]))
  ];

  buildPhase = ''
    rm -rf ./ISS/static;
    cp -r ${issStatic}/lib/node_modules/iss-static/dist ./ISS/static;
  '';

  installPhase = ''
    mkdir -p $out;
    cp -r ./ISS $out/ISS;
    cp ./manage.py $out/manage.py;
  '';
}
