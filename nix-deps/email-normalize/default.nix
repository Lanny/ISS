{ python3Packages, fetchFromGitHub }:
with python3Packages;
buildPythonPackage rec {
  name = "email-normalize";
  version = "2.0.0";

  doCheck = false;

  src = fetchFromGitHub {
    owner = "gmr";
    repo = "email-normalize";
    rev = version;
    sha256 = "sha256-mN+RCjyCeH5QijJTH3fKYyc8cemayf5VCH6gS5g5tgo=";
  };

  propagatedBuildInputs = [ aiodns ];
}

