class Krm < Formula
  desc "Monitor Kubernetes resource usage in the terminal"
  homepage "https://github.com/mikeoertli/kube-resource-monitor"
  url "https://github.com/mikeoertli/kube-resource-monitor/archive/b3fc8f4025347fc6a5ab549a98f263c3c2a86b26.tar.gz"
  version "1.4.0"
  sha256 "c889284b02246436083811204e27bc7bc6d25f1594f7f32159b792908dad3ba8"
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
