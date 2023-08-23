{ python3Packages }:
with python3Packages;
buildPythonPackage rec {
  pname = "bbcode";
  version = "1.1.0";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-6sT7HQ9sfOXEHktcBSJWKxWhrANvuRMa3Fnpoox9wdA=";
  };
}
