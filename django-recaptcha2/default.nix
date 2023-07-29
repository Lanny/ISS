{ python3Packages, fetchFromGitHub }:
with python3Packages;
buildPythonPackage rec {
  pname = "django-recaptcha2";
  version = "1.4.1";

  doCheck = false;

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-wLQ4UbBca/brtezIkME8ztrNm7M9ZLQpHHTdb8vIk2Y=";
  };

  propagatedBuildInputs = [
    requests
  ];
}

