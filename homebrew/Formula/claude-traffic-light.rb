class ClaudeTrafficLight < Formula
  include Language::Python::Virtualenv

  desc "macOS menu bar dot showing what Claude Code is doing right now"
  homepage "https://github.com/sidsimharaju/claude-traffic-light"
  # NOTE: url/sha256 point at a tagged GitHub release tarball. Bump both
  # together when cutting a new release — GitHub's release archive
  # checksums are stable once published, but only after the tag exists.
  url "https://github.com/sidsimharaju/claude-traffic-light/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "687c7b681b589a1dd8b21b9e6253a9a0240ad5f87a27d18a6620eab2eb95cef7"
  license "MIT"

  depends_on "python@3.13"

  resource "rumps" do
    url "https://files.pythonhosted.org/packages/b2/e2/2e6a47951290bd1a2831dcc50aec4b25d104c0cf00e8b7868cbd29cf3bfe/rumps-0.4.0.tar.gz"
    sha256 "17fb33c21b54b1e25db0d71d1d793dc19dc3c0b7d8c79dc6d833d0cffc8b1596"
  end

  resource "pyobjc-core" do
    url "https://files.pythonhosted.org/packages/a5/78/abc4ce5920305780aeb36b4067a86253378b36e29ba96673a3deb02eb03a/pyobjc_core-12.2.2.tar.gz"
    sha256 "3906452339cd06a3bb07df103c2511d4cb0f7a22d8771c0b802eba15d9a642b6"
  end

  resource "pyobjc-framework-cocoa" do
    url "https://files.pythonhosted.org/packages/75/76/49c6da2c6a831020b4854ba20079d5a1030474bffc776b7b73c2eeff8c15/pyobjc_framework_cocoa-12.2.2.tar.gz"
    sha256 "c96c0ef69a71afbbb0e6a7d594b455c5fe47d62e0db376ee7a2b4b828c16ace9"
  end

  def install
    virtualenv_install_with_resources
  end

  service do
    run [opt_bin/"claude-traffic-light", "run"]
    keep_alive false
    run_type :immediate
    log_path var/"log/claude-traffic-light.log"
    error_log_path var/"log/claude-traffic-light.err.log"
  end

  def caveats
    <<~EOS
      Register the Claude Code hooks that drive the menu bar dot (one-time,
      safe to re-run, and per-user — do this as whichever user runs Claude
      Code):
        claude-traffic-light install-hooks

      Then start the menu bar app:
        brew services start claude-traffic-light

      To remove the hooks again (e.g. before `brew uninstall`):
        claude-traffic-light uninstall-hooks
    EOS
  end

  test do
    system bin/"claude-traffic-light", "--help"
  end
end
