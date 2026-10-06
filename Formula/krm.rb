class Krm < Formula
  desc "Monitor Kubernetes resource usage in the terminal"
  homepage "https://github.com/mikeoertli/kube-resource-monitor"
  url "https://github.com/mikeoertli/kube-resource-monitor/archive/70b2b38fe036670cc93a3f110ad96cf10e31e1fa.tar.gz"
  version "1.2.1"
  sha256 "aa15a668672878ef3db94dc90cb2a505a764672682d724fbadba8daebf3b1690"
  license "MIT"
  head "https://github.com/mikeoertli/kube-resource-monitor.git", branch: "main"

  depends_on "go" => :build

  def install
    module_name = File.read("go.mod")[/^module\s+(\S+)/, 1]
    ldflags = %W[
      -s -w
      -X #{module_name}/internal/buildinfo.version=v#{version}
    ]
    system "go", "build", *std_go_args(ldflags:), "./cmd/krm"
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/krm version --short")
    assert_match "Usage:", shell_output("#{bin}/krm --help")
  end
end
