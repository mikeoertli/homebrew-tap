class ShellCharmProgress < Formula
  desc "Display terminal progress from shell scripts"
  homepage "https://github.com/mikeoertli/shell-charm-progress"
  url "https://github.com/mikeoertli/shell-charm-progress/archive/f1b6e42bcc2d4d1ddacf25101446ade831475494.tar.gz"
  version "1.0.0"
  sha256 "80f9da4d79b68393ad94b7c291d441642e42eb8cbabc87db774841414c3e6fae"
  head "https://github.com/mikeoertli/shell-charm-progress.git", branch: "main"

  depends_on "go" => :build

  def install
    system "go", "build", *std_go_args, "."
  end

  def caveats
    <<~EOS
      Load the shell helper in scripts that use the progress functions:
        eval "$(shell-charm-progress init)"
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/shell-charm-progress --version") unless build.head?
    assert_match "progress", shell_output("#{bin}/shell-charm-progress init")
  end
end
