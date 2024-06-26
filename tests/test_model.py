from thoughtspot_tml import Model
from ward import test # type: ignore

from . import _const


for version, file in ("V2", _const.DUMMY_MODEL):

    @test("Worksheet {version} deep attribute access")
    def _(file=file, version=version):
        t = Model.load(file)

        assert type(t) is Model

        t.guid
        t.model
        t.model.formulas
        t.model.formulas[0].expr
        t.model.columns
        t.model.columns[0].properties
        t.model.columns[0].properties.column_type
        t.model.columns[0].properties.index_type
        t.model.properties
        t.model.properties.is_bypass_rls


        if version == "V2":
            assert t.is_model is True
            t.model.schema
            t.model.schema.model_tables
            t.model.schema.model_tables[0].name
            t.model.schema.model_tables[0].alias
