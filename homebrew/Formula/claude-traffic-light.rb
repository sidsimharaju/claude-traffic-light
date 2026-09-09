class ClaudeTrafficLight < Formula
  include Language::Python::Virtualenv

  desc "macOS menu bar dot showing what Claude Code is doing right now"
  homepage "https://github.com/sidsimharaju/claude-traffic-light"
  # NOTE: url/sha256 point at a tagged GitHub release tarball. Bump both
  # together when cutting a new release — GitHub's release archive
  # checksums are stable once published, but only after the tag exists.
  url "https://github.com/sidsimharaju/claude-traffic-light/archive/refs/tags/v0.1.2.tar.gz"
  sha256 "47fce173ebeb81e16368f4d650bfe7eb01014e536271baff698d64498c679989"
  license "MIT"

  depends_on "python@3.13"

  resource "rumps" do
    url "https://files.pythonhosted.org/packages/b2/e2/2e6a47951290bd1a2831dcc50aec4b25d104c0cf00e8b7868cbd29cf3bfe/rumps-0.4.0.tar.gz"
    sha256 "17fb33c21b54b1e25db0d71d1d793dc19dc3c0b7d8c79dc6d833d0cffc8b1596"
  end

  # IMPORTANT: these must be source tarballs (sdist), not prebuilt wheels.
  # An earlier version of this formula pointed these at prebuilt
  # macosx-cp313 wheels to dodge the C compiler — that broke installs
  # entirely. Homebrew's own pip_install (Library/Homebrew/language/
  # python.rb) only installs a resource's wheel file directly when its URL
  # matches a *pure-Python* wheel (`*-py3-none-any.whl`); anything else —
  # including a platform-specific wheel like ours — gets unpacked as a
  # plain zip and then handed to `pip install --no-binary=:all:` as if it
  # were a source dist. A wheel has no setup.py/pyproject.toml, so that
  # always fails. Compiled Python extensions installed via
  # virtualenv_install_with_resources have to be sdists, built from source
  # against the active Xcode Command Line Tools — that's inherent to how
  # Homebrew formulae work, not something to route around.
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

  # Registers the Claude Code hooks and starts the menu bar app right
  # after `brew install` — the whole point of packaging this is a single
  # command, so don't make the user chase three more steps for it.
  # `install-hooks` is idempotent (safe on brew upgrade/reinstall too).
  # Neither step aborts the install if it fails — worst case, the caveats
  # below show the same two commands to run by hand.
  def post_install
    begin
      system bin/"claude-traffic-light", "install-hooks"
    rescue => e
      opoo "claude-traffic-light: couldn't register hooks automatically (#{e}). " \
           "Run `claude-traffic-light install-hooks` yourself."
    end

    begin
      system HOMEBREW_BREW_FILE, "services", "start", name
    rescue => e
      opoo "claude-traffic-light: couldn't start the menu bar app automatically (#{e}). " \
           "Run `brew services start claude-traffic-light` yourself."
    end
  end

  def caveats
    <<~EOS
      Hooks are registered in ~/.claude/settings.json and the menu bar app
      is running — open (or restart) a Claude Code session and the dot
      should turn green as soon as you submit a prompt.

      If either step above didn't happen (e.g. this ran non-interactively):
        claude-traffic-light install-hooks
        brew services start claude-traffic-light

      To remove the hooks again (e.g. before `brew uninstall`):
        claude-traffic-light uninstall-hooks
    EOS
  end

  test do
    system bin/"claude-traffic-light", "--help"
  end
end
