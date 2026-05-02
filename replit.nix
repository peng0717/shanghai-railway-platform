{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.flask
    pkgs.python310Packages.flask-sqlalchemy
    pkgs.python310Packages.flask-cors
  ];
}
