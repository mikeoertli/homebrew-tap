class Kcm < Formula
  desc "Manage Kubernetes contexts and profiles in your shell"
  homepage "https://github.com/mikeoertli/kube-context-manager"
  url "https://github.com/mikeoertli/kube-context-manager/archive/4d83d2fbb188d8c36d7983603adeb973f3643db4.tar.gz"
  version "0.6.0"
  sha256 "bcc491270d19f6fa6f0481fa8206db8caa906a651064a21742465ed4498bfb07"
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
