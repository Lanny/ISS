{ python3Packages }:
with python3Packages;
buildPythonPackage rec {
  pname = "tripphrase";
  version = "0.5";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-B1d+x1ixY3/a3oHEmJlLQiPK4l/aG4o7ckUUGrPbnRg=";
  };
}

