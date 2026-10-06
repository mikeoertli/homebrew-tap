class Kcm < Formula
  desc "Manage Kubernetes contexts and profiles in your shell"
  homepage "https://github.com/mikeoertli/kube-context-manager"
  url "https://github.com/mikeoertli/kube-context-manager/archive/9595d60ef63a940f0a92f14b14842cfbc2955445.tar.gz"
  version "0.4.0"
  sha256 "4947dec80d460016d61eb597071a513faf654256f5ccf65f9e8dc9c5f4ad5e8b"
  head "https://github.com/mikeoertli/kube-context-manager.git", branch: "main"

  depends_on "go" => :build
  depends_on "fzf"
  depends_on "kubernetes-cli"

  def install
    system "go", "build", *std_go_args, "./cmd/kcm"
  end

  def caveats
    <<~EOS
      Add shell integration after plugins and keybindings in ~/.zshrc:
        eval "$(kcm init zsh)"
      For Bash 4.4+, use kcm init bash in ~/.bashrc.
      Run kcm settings init to customize profiles.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/kcm version") unless build.head?
    assert_match "KUBECONFIG", shell_output("#{bin}/kcm init zsh")
  end
end
