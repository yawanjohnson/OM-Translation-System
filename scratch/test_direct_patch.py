import json
import os
from modules.idml_patcher import patch_idml

idml_path = "uploads/patch_028b1f39879844ea9aaf442661f73598.idml"
out_idml = "outputs/test_direct.idml"
out_excel = "outputs/test_direct_report.xlsx"

# Minimal instructions with a warning
instructions = [
    {
        'lang_code': 'CHT',
        'find': 'Heart rate monitoring systems may be inaccurate. Over exercising may result in serious injury or death. If you feel paint stop exercising immediately',
        'replace': 'Heart rate monitoring systems may be inaccurate. Over exercising may result in serious injury or death. If you feel paint stop exercising immediately',
        'note': 'DB Similar Found (ID: 812, Similarity: 99%): Heart rate monitoring systems may be inaccurate. Over exercising may result in serious injury or death. If you feel pain stop exercising immediately.',
        'mark_red': False,
        'mark_green': False,
        'mark_orange': True,
        'exact_match': True,
    }
]

print("Calling patch_idml directly...")
res = patch_idml(idml_path, instructions, out_idml, out_excel)
print("Finished. Excel report exists:", os.path.exists(out_excel))
