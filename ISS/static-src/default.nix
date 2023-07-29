{ buildNpmPackage }:
buildNpmPackage rec {
  name = "ISS-static";
  version = "1.0.0";
  src = ./.;

  npmDepsHash = "sha256-cgBQReGimtqMEyu+xNshFBcmgBdu63FgCyET/unNXNY=";

  npmBuildFlags = "--out-dir=\"./dist\"";
}
