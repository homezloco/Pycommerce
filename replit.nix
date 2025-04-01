{pkgs}: {
  deps = [
    pkgs.jq
    pkgs.rustc
    pkgs.pkg-config
    pkgs.libiconv
    pkgs.cargo
    pkgs.libxcrypt
    pkgs.postgresql
    pkgs.openssl
  ];
}
