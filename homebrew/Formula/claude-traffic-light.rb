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

  # Prebuilt universal2 wheels, not sdists: pyobjc-core has C extensions,
  # and building it from source needs a C compiler new enough to match the
  # active Xcode Command Line Tools — a real, avoidable install failure we
  # hit during testing on a machine with older CLTs. PyPI already ships a
  # cp313 universal2 wheel, so skip compiling entirely.
  resource "pyobjc-core" do
    url "https://files.pythonhosted.org/packages/1b/ed/a8bf040caf3704023d74086b7fb96cf4ed2e844e24bd94e5248ba214b700/pyobjc_core-12.2.2-cp313-cp313-macosx_10_13_universal2.whl"
    sha256 "950bd2d9c74634398c4e3d24ef2f213d4e23d705083697464fa67afedc53c1ad"
  end

  resource "pyobjc-framework-cocoa" do
    url "https://files.pythonhosted.org/packages/db/e1/5d9b04ebb60042b9cb49adc2d33115e2f2c2e4ff7d548017bfaff8b7f536/pyobjc_framework_cocoa-12.2.2-cp313-cp313-macosx_10_13_universal2.whl"
    sha256 "600b1723184ca094931330e79355274949965460e23de38628d601b5a967baf9"
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
