class ShellCharmProgress < Formula
  desc "Display terminal progress from shell scripts"
  homepage "https://github.com/mikeoertli/shell-charm-progress"
  url "https://github.com/mikeoertli/shell-charm-progress/archive/681033c27709be3c7957185021c1a47ba8773b13.tar.gz"
  version "1.1.0"
  sha256 "6f7347b0c9ba05566daa462b43f38704d6e1a9c894f8421a19abce39f9b86b37"
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
