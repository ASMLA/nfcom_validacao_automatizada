class CT005_cClassTrib:
    def validar(self, item, resultado_item, classificacao):
        imp = item.get("IMPOSTO_REFORMA", {})
        ctrib_json = str(imp.get("COD_CLASSIF_TRIB", "")).strip()
        ctrib_esp = classificacao.get("cclass_esperado")

        if ctrib_json != ctrib_esp:
            resultado_item["CT005"] = {
                "erro": True,
                "esperado": ctrib_esp,
                "encontrado": ctrib_json
            }
        else:
            resultado_item["CT005"] = {
                "erro": False,
                "esperado": ctrib_esp,
                "encontrado": ctrib_json
            }
