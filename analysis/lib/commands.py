"""Original command-occurrence counting, including its audited fragment."""
import trace as parser
AUDITED_SLOT="1121:r03"
AUDITED_TOOL="toolu_01VEp1Bbg2bd6K6CSQ3EPi2y"
AUDITED_ARGS=["src/org/sosy_lab/solver/z3/","2",">","/dev/null"]

def split_commands(command, slot_id="", tool_id=""):
    kept, excluded = [], []
    for invocation in parser.parse_shell_invocations(command):
        reason = None
        if invocation["executable"] in {"done", "2", "#"}:
            reason = "historically audited shell syntax fragment"
        if (slot_id == AUDITED_SLOT and tool_id == AUDITED_TOOL
                and invocation["executable"] == "--" and invocation["arguments"] == AUDITED_ARGS):
            assert '$(git rev-list -n1 3e4655d) -- src/org/sosy_lab/solver/z3/' in command
            reason = "audited enclosing git-grep arguments after command substitution"
        if reason:
            excluded.append(dict(invocation=invocation, reason=reason))
        else:
            kept.append(invocation)
    return kept, excluded
