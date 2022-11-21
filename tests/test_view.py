from thoughtspot_tml import View
from ward import test

from . import _const


@test("View deep attribute access")
def _():
    t = View.load(_const.DUMMY_VIEW)

    assert type(t) is View

    t.guid
    t.view
    t.view.search_query
    t.view.formulas
    t.view.formulas[0].expr
    t.view.view_columns
    t.view.view_columns[0].search_output_column
    t.view.view_columns[0].properties
    t.view.view_columns[0].properties.column_type
    t.view.joins_with
    t.view.joins_with[0].destination
    t.view.joins_with[0].destination.name


@test("View roundtrips")
def _():
    before_t = _const.DUMMY_VIEW.read_text()
    t = View.loads(before_t)
    after_t = t.dumps()

    assert type(before_t) is str
    assert type(t) is View
    assert type(after_t) is str
    assert before_t == after_t
