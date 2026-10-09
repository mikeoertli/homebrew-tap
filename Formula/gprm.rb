class Gprm < Formula
  desc "Monitor GitHub pull requests and CI in the terminal"
  homepage "https://github.com/mikeoertli/github-pr-monitor"
  url "https://github.com/mikeoertli/github-pr-monitor/archive/61b58a57efb861e32b125c3adfb966641511c0b2.tar.gz"
  version "1.2.0"
  sha256 "6426a53f55bf61b7151d1549e02f353168482fd98e9b7dd1c88f9ca6f36a347c"
  head "https://github.com/mikeoertli/github-pr-monitor.git", branch: "main"

  depends_on "go" => :build
  depends_on "gh"

  def install
    system "go", "build", *std_go_args, "./cmd/gprm"
    bin.install_symlink "gprm" => "ghprm"
    bin.install_symlink "gprm" => "github-pr-monitor"
    generate_completions_from_executable(bin/"gprm", "completion")
    bash_completion.install_symlink "gprm" => "ghprm"
    bash_completion.install_symlink "gprm" => "github-pr-monitor"
    fish_completion.install_symlink "gprm.fish" => "ghprm.fish"
    fish_completion.install_symlink "gprm.fish" => "github-pr-monitor.fish"
    (pkgshare/"completions").mkpath
    (pkgshare/"completions/gprm.ps1").write Utils.safe_popen_read(bin/"gprm", "completion", "powershell")
  end

  def caveats
    <<~EOS
      Authenticate before live monitoring:
        gh auth login
      The gprm, ghprm, and github-pr-monitor commands are installed.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/gprm --version") unless build.head?
    assert_match "gprm", shell_output("#{bin}/ghprm --help 2>&1")
    assert_match "gprm", shell_output("#{bin}/github-pr-monitor --help 2>&1")
  end
end
