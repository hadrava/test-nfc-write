import copy
import tempfile
import subprocess
import yaml

class TagCreator:
    def __init__(self, mdb_path, opt_utils_path, opt_python_path):
        self._mdb_path = mdb_path
        self._opt_utils_path = opt_utils_path
        self._opt_python_path = opt_python_path

        self._data_for_products = {
                17558: {
                    # Material information
                    "material_class": "FFF",
                    "material_type": "PETG",
                    "brand_name": "Prusament",
                    "material_name": "PETG Jet Black",
                    "primary_color": {
                        "hex": "24292A",
                    },
                    "tags": [],
                    "density": 1270,

                    # Package-spcific fields
                    "gtin": "8594173675100",
                    "nominal_netto_full_weight": 1000,

                    # Printing parameters
                    "min_print_temperature": 240,
                    "max_print_temperature": 260,
                    "min_bed_temperature": 70,
                    "max_bed_temperature": 90,
                    "preheat_temperature": 170,
                    "chamber_temperature": 35,
                    "min_chamber_temperature": 18,
                    "max_chamber_temperature": 60,

                    # Container info
                    "empty_container_weight": 280,
                    "container_outer_diameter": 200,
                    "container_inner_diameter": 100,
                    "container_hole_diameter": 52,
                    "container_width": 64,

                    # Support metadata
                    "write_protection": "protect_page_unlockable",
                },
            }

    def create_tag(self, spool_info):
        prod_info = self._data_for_products.get(int(spool_info.final_ff_goods_id))
        if prod_info is None:
            raise Exception("Tento produkt se nepodařilo najít v materiálové databázi.")

        spool_data = copy.deepcopy(prod_info)

        spool_data['brand_specific_instance_id'] = spool_info.spool_unique_id
        spool_data['manufactured_date'] = int(spool_info.cut_timestamp)
        spool_data['actual_netto_full_weight'] = int(spool_info.filament_weight)

        with tempfile.NamedTemporaryFile(suffix='.yaml') as temp:
            temp.write(yaml.dump({"data": { "main": spool_data}}).encode())
            temp.flush()

            uri = f"https://3dtag.org/s/{spool_info.spool_unique_id}"

            proc = subprocess.Popen(
                    f"{self._opt_python_path} nfc_initialize.py --size=312 --aux-region=32 --ndef-uri={uri} | " +
                    f"{self._opt_python_path} rec_update.py {temp.name}",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=f"{self._opt_utils_path}",
                    shell=True,
                    )

            stdout, stderr = proc.communicate()
            returncode = proc.returncode

            if returncode != 0:
                err = f"Nepodařilo se vygenerovat data pro cívku {spool_info.spool_unique_id} (spool_info.final_ff_goods_id) (returncode: {returncode})"
                print(err)
                print(stderr)
                raise Exception(err)

            if stderr != b'':
                err = f"Nepodařilo se vygenerovat data pro cívku {spool_info.spool_unique_id} (spool_info.final_ff_goods_id) (stderr: {len(stderr)})"
                print(err)
                print(stderr)
                raise Exception(err)

            tag_content = stdout
            print(f"tag_len: {len(tag_content)}")
            print(tag_content)

            ### Validation

            fields_check_file = "../tests/specific/missing_required_fields.yaml" # TODO XXX: which fields should be checked?
            proc = subprocess.Popen(
                    f"{self._opt_python_path} rec_info.py --show-all --validate --extra-required-fields={fields_check_file}",
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=f"{self._opt_utils_path}",
                    shell=True,
                    )

            stdout, stderr = proc.communicate(input=tag_content)
            returncode = proc.returncode

            if returncode != 0:
                err = f"Nepodařilo se zvalidovat vygenerovaná data pro cívku {spool_info.spool_unique_id} (spool_info.final_ff_goods_id) (returncode: {returncode})"
                print(err)
                print(stdout)
                print(stderr)
                raise Exception(err)

            if stderr != b'':
                err = f"Nepodařilo se zvalidovat vygenerovaná data pro cívku {spool_info.spool_unique_id} (spool_info.final_ff_goods_id) (stderr: {len(stderr)})"
                print(err)
                print(stdout)
                print(stderr)
                raise Exception(err)

        return tag_content

        ### DEBUG:
        #return b'\x043dtag.org/s/' + spool_info.spool_unique_id.encode();

        #with open('/tmp/a.bin', 'rb') as f:
        #    data_to_write = f.read()

        #ar = [225, 64, 40, 1, 3, 255, 308 //256, 308 %256]
        #return bytes(ar) + data_to_write
        #return b'\x043dtag.org/s/' + spool_info.spool_unique_id.encode() + b'\x00'*180;
