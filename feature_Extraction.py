# The given Code extracts all features of .apk file
from androguard.core.bytecodes.dvm import DalvikVMFormat
from androguard.core.analysis.analysis import Analysis
from androguard.decompiler.decompiler import DecompilerDAD
from androguard.core.bytecodes.apk import APK
from androguard.core.analysis import analysis
from constants import SPECIAL_STRINGS, DB_REGEX, API_CALLS, PERMISSIONS, INTENTS
import math
import hashlib


def extract_features(file_path):
    result = {}
    try:
        a = APK(file_path)
        d = DalvikVMFormat(a.get_dex())
        dx = Analysis(d)
        d.set_vmanalysis(dx)
        d.set_decompiler(DecompilerDAD(d, dx))
    except:
        return None

    result['android_version_code'] = a.get_androidversion_code()
    result['android_version_name'] = a.get_androidversion_name()
    result['max_sdk'] = a.get_max_sdk_version()
    result['min_sdk'] = a.get_min_sdk_version()
    result['filename'] = a.get_filename()
    result['target_sdk'] = a.get_target_sdk_version()
    result['md5'] = hashlib.md5(a.get_raw()).hexdigest()
    result['sha256'] = hashlib.sha256(a.get_raw()).hexdigest()
    result['permissions'] = a.get_permissions()
    result['activities'] = a.get_activities()
    result['providers'] = a.get_providers()
    result['services'] = a.get_services()
    result['strings'] = d.get_strings()
    result['class_names'] = [c.get_name() for c in d.get_classes()]
    result['method_names'] = [m.get_name() for m in d.get_methods()]
    result['field_names'] = [f.get_name() for f in d.get_fields()]
    result['is_obfuscation'] = 1 if analysis.is_ascii_obfuscation(d) else 0
    '''result['is_dyn_code'] = 1 if analysis.is_dyn_code(dx) else 0
    result['is_reflection_code'] = 1 if analysis.is_reflection_code(vmx) else 0'''
    result['is_database'] = 1 if d.get_regex_strings(DB_REGEX) else 0
    arr = []
    s = a.get_elements("action", "name")
    for i in s:
        arr.append(i)

    result['intents'] = arr
    s_list = []
    s_list.extend(result['class_names'])
    s_list.extend(result['method_names'])
    s_list.extend(result['field_names'])
    result['entropy_rate'] = entropy_rate(s_list)
    result['feature_vectors'] = {}
    result['feature_vectors']['api_calls'] = []
    for call in API_CALLS:
        status = 1 if dx.get_method(call) else 0
        result['feature_vectors']['api_calls'].append(status)
    result['feature_vectors']['permissions'] = []
    for permission in PERMISSIONS:
        status = 1 if permission in result['permissions'] else 0
        result['feature_vectors']['permissions'].append(status)
    result['feature_vectors']['intents']=[]
    n = len(INTENTS)
    m = len(result['intents'])
    for i in range(n):
        stri = INTENTS[i]
        flg = False
        for j in range(m):
            if stri in result['intents'][j]:
                flg = True
                break
        if flg:
            status=1
        else:
            status=0
        result['feature_vectors']['intents'].append(status)
    result['feature_vectors']['special_strings'] = []
    for word in SPECIAL_STRINGS:
        status = 1 if d.get_regex_strings(word) else 0
        result['feature_vectors']['special_strings'].append(status)

    return result
def entropy_rate(data):
    for s in data:
        prob = [float(s.count(c)) / len(s) for c in dict.fromkeys(list(s))]
        entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
        p = 1.0 / len(data)
        idealize = -1.0 * len(data) * p * math.log(p) / math.log(2.0)
        return round((abs(idealize) - entropy) / idealize, 2)
def create_vector_single(apk):
    feature_vector = []
    feature_vector.extend(apk['feature_vectors']['permissions'])
    feature_vector.extend(apk['feature_vectors']['api_calls'])
    feature_vector.extend(apk['feature_vectors']['intents'])
    feature_vector.extend(apk['feature_vectors']['special_strings'])

    entropy_rate = int(apk['entropy_rate'])
    db = int(apk['is_database'])
    feature_vector.append(entropy_rate)
    feature_vector.append(db)
    return feature_vector
def create_vector_multiple(data):
    feature_vector = []
    target_vector = []
    for apk in data:
        apk_vector = []
        apk_vector.extend(apk['feature_vectors']['permissions'])
        apk_vector.extend(apk['feature_vectors']['api_calls'])
        apk_vector.extend(apk['feature_vectors']['intents'])
        apk_vector.extend(apk['feature_vectors']['special_strings'])
        entropy_rate = int(apk['entropy_rate'])
        db = int(apk['is_database'])
        apk_vector.append(entropy_rate)
        apk_vector.append(db)
        target_type = 1 if apk['data_type'] == 'malware' else 0
        feature_vector.append(apk_vector)
        target_vector.append(target_type)
    return feature_vector, target_vector
