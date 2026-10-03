import pytest
from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine


def test_flow_condition_evaluation():
    interp = OqlInterpreter(variables={"_status": 500, "base_url": "http://127.0.0.1:8787"})
    logs = []
    interp.out.info = lambda msg: logs.append(msg)

    # Truthy condition
    line = OqlLine(number=1, command="IF", args="_status >= 500 THEN LOG 'Server error detected'", raw="IF _status >= 500 THEN LOG 'Server error detected'")
    interp._cmd_if(line.args, line)
    assert logs == ["Server error detected"]

    # Falsy condition
    line2 = OqlLine(number=2, command="IF", args="_status == 200 THEN LOG 'OK'", raw="IF _status == 200 THEN LOG 'OK'")
    interp._cmd_if(line2.args, line2)
    assert logs == ["Server error detected"]


def test_testtoon_flow_condition_expansion():
    from testql.interpreter._testtoon_parser import testtoon_to_oql

    toon_text = """TESTTOON: 1.0
SCENARIO: Test Flow
FLOW[1]{condition, action}:
  _status >= 500, LOG 'Server error'
"""
    script = testtoon_to_oql(toon_text)
    commands = [(l.command, l.args) for l in script.lines]
    assert any(c[0] == "IF" and "_status >= 500 THEN LOG 'Server error'" in c[1] for c in commands)
