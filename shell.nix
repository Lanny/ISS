let 
  pkgs = import <nixpkgs> {};
  issStatic = (pkgs.callPackage ./ISS/static-src {});
in
pkgs.stdenv.mkDerivation {
  name = "ISS";
  buildInputs = [
    pkgs.nodejs-18_x
    (pkgs.python3.withPackages( ps: with ps; [
      build
      django
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
    ]))
  ];

  nativeBuildInputs = [
    pkgs.postgresql_15
  ];

  postgresConf =
    pkgs.writeText "postgresql.conf"
      ''
        # Add Custom Settings
        log_min_messages = warning
        log_min_error_statement = error
        log_min_duration_statement = 100  # ms
        log_connections = on
        log_disconnections = on
        log_duration = on
        #log_line_prefix = '[] '
        log_timezone = 'UTC'
        log_statement = 'all'
        log_directory = 'pg_log'
        log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
        logging_collector = on
        log_min_error_statement = error
      '';


  PGDATA = "${toString ./.}/.pg";

  # Post Shell Hook
  shellHook = ''
    echo "Using ${pkgs.postgresql_15.name}."

    export ISS_SETTINGS_FILE=$(pwd)/settings.py
    # Setup: other env variables
    export PGHOST="$PGDATA"

    npm config set prefix /home/lanny/.node/18.x

    # Setup: DB
    [ ! -d $PGDATA ] && pg_ctl initdb -o "-U postgres" && cat "$postgresConf" >> $PGDATA/postgresql.conf
    pg_ctl -o "-p 5432 -k $PGDATA" start

    alias fin="pg_ctl stop && exit"
    alias pg="psql -p 5432 -U postgres"
  '';
}


