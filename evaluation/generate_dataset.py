"""
Generate evaluation dataset — incidents + ground truth.
Run once to populate evaluation/incidents/ and evaluation/ground_truth/.
"""
import os, json

BASE = os.path.dirname(os.path.abspath(__file__))
INC_DIR = os.path.join(BASE, "incidents")
GT_DIR  = os.path.join(BASE, "ground_truth")

DATA = [
    # 003 - Sri Lanka Easter Bombings
    {
        "text": "On 21 April 2019, Easter Sunday, a series of coordinated suicide bombings struck three churches and three luxury hotels in Sri Lanka. The attacks targeted St. Anthony's Church in Colombo, St. Sebastian's Church in Negombo, Zion Church in Batticaloa, the Shangri-La Hotel, Cinnamon Grand Hotel, and Kingsbury Hotel in Colombo. The National Thowheed Jamath carried out the attacks with support from the Islamic State. At least 269 people were killed and over 500 were injured in the blasts.",
        "gt": {
            "date": "2019-04-21",
            "country": "Sri Lanka",
            "state": "",
            "city": "Colombo",
            "responsible_groups": ["National Thowheed Jamath", "Islamic State"],
            "target_organizations": [],
            "killed": 269,
            "injured": 500,
            "attack_types": ["Bombing"],
            "weapon_types": ["Explosives"],
            "target_types": ["Religious", "Civilian"]
        }
    },
    # 004 - Pathankot Airbase Attack
    {
        "text": "On 2 January 2016, a group of armed militants attacked the Indian Air Force base at Pathankot in Punjab, India. The attackers, affiliated with Jaish-e-Mohammed, breached the perimeter and engaged in a prolonged gunfight with Indian security forces. Seven Indian Air Force personnel and security forces were killed and 22 others were injured. All six attackers were killed in the operation. The attack was believed to have been planned in Pakistan.",
        "gt": {
            "date": "2016-01-02",
            "country": "India",
            "state": "Punjab",
            "city": "Pathankot",
            "responsible_groups": ["Jaish-e-Mohammed"],
            "target_organizations": ["Indian Air Force"],
            "killed": 7,
            "injured": 22,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms"],
            "target_types": ["Military"]
        }
    },
    # 005 - Peshawar School Massacre
    {
        "text": "On 16 December 2014, six gunmen affiliated with the Tehrik-i-Taliban Pakistan entered the Army Public School in Peshawar, Pakistan. The militants carried out a systematic massacre of schoolchildren and staff. A total of 149 people were killed, including 132 children, and at least 114 were injured. The Pakistani Army launched a rescue operation that lasted several hours. All six attackers were killed by security forces.",
        "gt": {
            "date": "2014-12-16",
            "country": "Pakistan",
            "state": "",
            "city": "Peshawar",
            "responsible_groups": ["Tehrik-i-Taliban Pakistan"],
            "target_organizations": [],
            "killed": 149,
            "injured": 114,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms"],
            "target_types": ["Civilian"]
        }
    },
    # 006 - Uri Attack
    {
        "text": "On 18 September 2016, four militants attacked an Indian Army brigade headquarters near the town of Uri in Jammu and Kashmir. The militants, later identified as members of Jaish-e-Mohammed from Pakistan, threw grenades and opened fire on the camp in the early morning hours. 19 Indian Army soldiers were killed and over 30 were injured, making it one of the deadliest attacks on Indian military forces in recent years. All four attackers were killed in the encounter.",
        "gt": {
            "date": "2016-09-18",
            "country": "India",
            "state": "Jammu",
            "city": "Uri",
            "responsible_groups": ["Jaish-e-Mohammed"],
            "target_organizations": ["Indian Army"],
            "killed": 19,
            "injured": 30,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms", "Explosives"],
            "target_types": ["Military"]
        }
    },
    # 007 - Kabul Airport Attack
    {
        "text": "On 26 August 2021, a suicide bombing took place outside Hamid Karzai International Airport in Kabul, Afghanistan during the United States military evacuation. The Islamic State Khorasan Province claimed responsibility for the attack. At least 183 people were killed, including 13 US military service members, and more than 150 were wounded. The blast targeted crowds of Afghan civilians gathered near the Abbey Gate seeking evacuation flights.",
        "gt": {
            "date": "2021-08-26",
            "country": "Afghanistan",
            "state": "",
            "city": "Kabul",
            "responsible_groups": ["Islamic State Khorasan Province"],
            "target_organizations": [],
            "killed": 183,
            "injured": 150,
            "attack_types": ["Bombing"],
            "weapon_types": ["Explosives"],
            "target_types": ["Civilian", "Military"]
        }
    },
    # 008 - Quetta Police Academy Attack
    {
        "text": "On 25 October 2016, three militants stormed the Police Training College in Quetta, Balochistan, Pakistan. The attackers, affiliated with the Islamic State, opened fire on sleeping cadets in their dormitories. At least 61 cadets were killed and more than 117 were injured. Pakistani security forces launched a counter-operation that lasted several hours before all three attackers were neutralized.",
        "gt": {
            "date": "2016-10-25",
            "country": "Pakistan",
            "state": "Balochistan",
            "city": "Quetta",
            "responsible_groups": ["Islamic State"],
            "target_organizations": ["Police"],
            "killed": 61,
            "injured": 117,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms"],
            "target_types": ["Government"]
        }
    },
    # 009 - Dhaka Bakery Attack
    {
        "text": "On 1 July 2016, a group of five militants affiliated with the Islamic State attacked the Holey Artisan Bakery in the diplomatic quarter of Dhaka, Bangladesh. The attackers took hostages and killed 22 people, including 17 foreign nationals, and injured 50 others. Bangladeshi security forces launched a rescue operation the following morning, killing all five attackers. The victims included citizens from Japan, Italy, India, and the United States.",
        "gt": {
            "date": "2016-07-01",
            "country": "Bangladesh",
            "state": "",
            "city": "Dhaka",
            "responsible_groups": ["Islamic State"],
            "target_organizations": [],
            "killed": 22,
            "injured": 50,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms"],
            "target_types": ["Civilian"]
        }
    },
    # 010 - Indian Parliament Attack
    {
        "text": "On 13 December 2001, five armed militants attacked the Indian Parliament building in New Delhi, India. The attackers, believed to be members of Lashkar-e-Taiba and Jaish-e-Mohammed, opened fire and detonated explosives near the Parliament entrance. Nine people were killed, including security personnel from the Parliament Security Service, Delhi Police, and CRPF, and 18 others were injured. All five attackers were shot dead by security forces.",
        "gt": {
            "date": "2001-12-13",
            "country": "India",
            "state": "",
            "city": "New Delhi",
            "responsible_groups": ["Lashkar-e-Taiba", "Jaish-e-Mohammed"],
            "target_organizations": ["Delhi Police", "CRPF"],
            "killed": 9,
            "injured": 18,
            "attack_types": ["Armed Assault", "Bombing"],
            "weapon_types": ["Firearms", "Explosives"],
            "target_types": ["Government"]
        }
    },
    # 011 - Lahore Park Bombing
    {
        "text": "On 27 March 2016, a suicide bomber detonated an explosive device in Gulshan-e-Iqbal Park in Lahore, Pakistan, on Easter Sunday. The park was crowded with families and children celebrating the holiday. Jamaat-ul-Ahrar, a faction of the Tehrik-i-Taliban Pakistan, claimed responsibility for the attack. At least 75 people were killed and more than 340 were injured in the blast.",
        "gt": {
            "date": "2016-03-27",
            "country": "Pakistan",
            "state": "",
            "city": "Lahore",
            "responsible_groups": ["Jamaat-ul-Ahrar"],
            "target_organizations": [],
            "killed": 75,
            "injured": 340,
            "attack_types": ["Bombing"],
            "weapon_types": ["Explosives"],
            "target_types": ["Civilian"]
        }
    },
    # 012 - Srinagar CRPF Camp Attack
    {
        "text": "On 3 October 2017, militants from Lashkar-e-Taiba attacked a CRPF camp on the outskirts of Srinagar in Jammu and Kashmir, India. The attackers used automatic weapons and grenades in the early morning assault. Two CRPF jawans were killed and four others were injured before the militants were neutralized in a gunfight lasting several hours.",
        "gt": {
            "date": "2017-10-03",
            "country": "India",
            "state": "Jammu",
            "city": "Srinagar",
            "responsible_groups": ["Lashkar-e-Taiba"],
            "target_organizations": ["CRPF"],
            "killed": 2,
            "injured": 4,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms", "Explosives"],
            "target_types": ["Military"]
        }
    },
    # 013 - Wagah Border Bombing
    {
        "text": "On 2 November 2014, a suicide bomber detonated an explosive vest near the Wagah border crossing on the Pakistani side, close to Lahore. The blast occurred as spectators were leaving after the daily flag-lowering ceremony. At least 60 people were killed and more than 110 were injured. Jundallah, a militant group with links to the Tehrik-i-Taliban Pakistan, claimed responsibility for the attack.",
        "gt": {
            "date": "2014-11-02",
            "country": "Pakistan",
            "state": "",
            "city": "Lahore",
            "responsible_groups": ["Jundallah"],
            "target_organizations": [],
            "killed": 60,
            "injured": 110,
            "attack_types": ["Bombing"],
            "weapon_types": ["Explosives"],
            "target_types": ["Civilian"]
        }
    },
    # 014 - Kandahar Guest House Attack
    {
        "text": "On 11 January 2017, Taliban militants carried out a car bomb and gun attack on a guest house used by Afghan intelligence officials in Kandahar, Afghanistan. The explosion destroyed parts of the building and was followed by gunfire from militants. At least 11 people were killed and 16 others were wounded. The Taliban claimed the attack was targeting Afghan National Directorate of Security officers.",
        "gt": {
            "date": "2017-01-11",
            "country": "Afghanistan",
            "state": "",
            "city": "Kandahar",
            "responsible_groups": ["Taliban"],
            "target_organizations": [],
            "killed": 11,
            "injured": 16,
            "attack_types": ["Bombing", "Armed Assault"],
            "weapon_types": ["Explosives", "Vehicle", "Firearms"],
            "target_types": ["Government"]
        }
    },
    # 015 - Bodh Gaya Bombing
    {
        "text": "On 7 July 2013, a series of low-intensity blasts struck the Mahabodhi Temple complex in Bodh Gaya, Bihar, India. Ten improvised explosive devices were planted around the Buddhist pilgrimage site, of which five detonated. Five monks were injured in the blasts but there were no fatalities. Indian Mujahideen was suspected of carrying out the attack, which was seen as retaliation for Buddhist violence against Muslims in Myanmar.",
        "gt": {
            "date": "2013-07-07",
            "country": "India",
            "state": "Bihar",
            "city": "Bodh Gaya",
            "responsible_groups": ["Indian Mujahideen"],
            "target_organizations": [],
            "killed": 0,
            "injured": 5,
            "attack_types": ["Bombing"],
            "weapon_types": ["Explosives"],
            "target_types": ["Religious"]
        }
    },
    # 016 - Kunduz Hospital Airstrike
    {
        "text": "On 3 October 2015, a United States Air Force AC-130 gunship attacked the Doctors Without Borders trauma centre in Kunduz, Afghanistan. The airstrike lasted over an hour and destroyed much of the hospital. At least 42 people were killed, including 14 staff members of Medecins Sans Frontieres, 24 patients, and 4 caretakers. An additional 37 people were injured. The Taliban had captured Kunduz city days earlier, and the area was an active combat zone.",
        "gt": {
            "date": "2015-10-03",
            "country": "Afghanistan",
            "state": "",
            "city": "Kunduz",
            "responsible_groups": [],
            "target_organizations": [],
            "killed": 42,
            "injured": 37,
            "attack_types": [],
            "weapon_types": [],
            "target_types": ["Civilian"]
        }
    },
    # 017 - Nagrota Army Camp Attack
    {
        "text": "On 29 November 2016, three Jaish-e-Mohammed militants attacked an Indian Army camp at Nagrota near Jammu city in Jammu and Kashmir. The militants entered the residential quarters and took hostages, including women and children. Seven people were killed, including three soldiers and two family members of army personnel, and 10 others were injured. All three militants were killed in the encounter.",
        "gt": {
            "date": "2016-11-29",
            "country": "India",
            "state": "Jammu",
            "city": "Nagrota",
            "responsible_groups": ["Jaish-e-Mohammed"],
            "target_organizations": ["Indian Army"],
            "killed": 7,
            "injured": 10,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms"],
            "target_types": ["Military"]
        }
    },
    # 018 - Kabul Military Hospital Attack
    {
        "text": "On 8 March 2017, gunmen wearing white lab coats and armed with automatic weapons and grenades attacked the Sardar Daud Khan Military Hospital in Kabul, Afghanistan. The Islamic State claimed responsibility for the attack. At least 49 people were killed and 63 were wounded. The attackers entered the 400-bed hospital through the main entrance and moved floor to floor shooting patients and staff.",
        "gt": {
            "date": "2017-03-08",
            "country": "Afghanistan",
            "state": "",
            "city": "Kabul",
            "responsible_groups": ["Islamic State"],
            "target_organizations": [],
            "killed": 49,
            "injured": 63,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms", "Explosives"],
            "target_types": ["Military", "Civilian"]
        }
    },
    # 019 - Amarnath Yatra Bus Attack
    {
        "text": "On 10 July 2017, militants from Lashkar-e-Taiba fired upon a bus carrying Amarnath Yatra pilgrims on the Anantnag-Srinagar highway in Jammu and Kashmir, India. Seven Hindu pilgrims were killed and 19 were injured in the attack. The bus was returning from the annual pilgrimage to the Amarnath cave shrine. Indian security forces launched a massive search operation in the area following the incident.",
        "gt": {
            "date": "2017-07-10",
            "country": "India",
            "state": "Jammu",
            "city": "Anantnag",
            "responsible_groups": ["Lashkar-e-Taiba"],
            "target_organizations": [],
            "killed": 7,
            "injured": 19,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms"],
            "target_types": ["Religious", "Civilian"]
        }
    },
    # 020 - Jalalabad Prison Attack
    {
        "text": "On 2 August 2020, Islamic State militants launched a complex assault on a prison in Jalalabad, the capital of Nangarhar province in eastern Afghanistan. The attack began with a car bomb explosion at the prison gate, followed by an armed assault by several gunmen. At least 29 people were killed and 50 others were wounded in the prolonged fighting. The attackers attempted to free hundreds of Islamic State prisoners held at the facility.",
        "gt": {
            "date": "2020-08-02",
            "country": "Afghanistan",
            "state": "Nangarhar",
            "city": "Jalalabad",
            "responsible_groups": ["Islamic State"],
            "target_organizations": [],
            "killed": 29,
            "injured": 50,
            "attack_types": ["Bombing", "Armed Assault"],
            "weapon_types": ["Explosives", "Vehicle", "Firearms"],
            "target_types": ["Government"]
        }
    },
    # 021 - Karachi Airport Attack
    {
        "text": "On 8 June 2014, ten heavily armed militants from the Tehrik-i-Taliban Pakistan attacked Jinnah International Airport in Karachi, Pakistan. The attackers, equipped with assault rifles, grenades, and rocket launchers, breached the airport perimeter and engaged security forces. At least 36 people were killed, including all ten attackers, and 18 others were injured. The Airport Security Force and Pakistan Rangers responded to the attack.",
        "gt": {
            "date": "2014-06-08",
            "country": "Pakistan",
            "state": "Sindh",
            "city": "Karachi",
            "responsible_groups": ["Tehrik-i-Taliban Pakistan"],
            "target_organizations": [],
            "killed": 36,
            "injured": 18,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms", "Explosives"],
            "target_types": ["Transportation"]
        }
    },
    # 022 - Gurdaspur Attack
    {
        "text": "On 27 July 2015, three militants dressed in Indian Army uniforms attacked a police station and a bus in Dinanagar town in Gurdaspur district, Punjab, India. The attackers opened fire on the bus and then laid siege to the police station. Seven people were killed, including three Punjab Police officers and a superintendent of police, and 15 were injured. The attack was attributed to militants linked to Pakistan-based Lashkar-e-Taiba.",
        "gt": {
            "date": "2015-07-27",
            "country": "India",
            "state": "Punjab",
            "city": "Gurdaspur",
            "responsible_groups": ["Lashkar-e-Taiba"],
            "target_organizations": ["Punjab Police"],
            "killed": 7,
            "injured": 15,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms"],
            "target_types": ["Government", "Civilian"]
        }
    },
    # 023 - Mazar-i-Sharif Consulate Attack
    {
        "text": "On 4 January 2018, a suicide car bomb targeted the Indian Consulate in Mazar-i-Sharif, Balkh province, Afghanistan. The Taliban claimed responsibility for the attack. The blast damaged the outer walls of the consulate compound. Two Afghan civilians were killed and 6 others were injured. Indian diplomatic staff inside the compound were unharmed. Afghan National Police and Indian security personnel secured the area.",
        "gt": {
            "date": "2018-01-04",
            "country": "Afghanistan",
            "state": "Balkh",
            "city": "Mazar-i-Sharif",
            "responsible_groups": ["Taliban"],
            "target_organizations": [],
            "killed": 2,
            "injured": 6,
            "attack_types": ["Bombing"],
            "weapon_types": ["Explosives", "Vehicle"],
            "target_types": ["Government"]
        }
    },
    # 024 - Chittagong Army Camp
    {
        "text": "On 22 December 2009, militants from the Bangladesh Rifles opened fire on army officers during a meeting at Pilkhana BDR headquarters in Dhaka, Bangladesh. The mutiny resulted in the deaths of 74 people, including 57 army officers. More than 50 others were injured during the day-long violence. The incident was characterized as an armed revolt rather than a terrorist attack, but it severely damaged military command structure.",
        "gt": {
            "date": "2009-12-22",
            "country": "Bangladesh",
            "state": "",
            "city": "Dhaka",
            "responsible_groups": ["Bangladesh Rifles"],
            "target_organizations": [],
            "killed": 74,
            "injured": 50,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms"],
            "target_types": ["Military"]
        }
    },
    # 025 - Handwara BSF Attack
    {
        "text": "On 5 April 2020, two Hizbul Mujahideen militants attacked a Border Security Force patrol near Handwara in Kupwara district of Jammu and Kashmir, India. The militants opened fire on the BSF vehicle, killing 3 BSF jawans and injuring 2 others. The attackers fled into a nearby forested area. Security forces launched a cordon and search operation in the surrounding villages.",
        "gt": {
            "date": "2020-04-05",
            "country": "India",
            "state": "Jammu",
            "city": "Handwara",
            "responsible_groups": ["Hizbul Mujahideen"],
            "target_organizations": ["BSF"],
            "killed": 3,
            "injured": 2,
            "attack_types": ["Armed Assault"],
            "weapon_types": ["Firearms"],
            "target_types": ["Military"]
        }
    },
]

for i, entry in enumerate(DATA, start=3):
    idx = f"{i:03d}"

    # Write incident text
    inc_path = os.path.join(INC_DIR, f"incident_{idx}.txt")
    with open(inc_path, "w") as f:
        f.write(entry["text"].strip() + "\n")

    # Write ground truth JSON
    gt_path = os.path.join(GT_DIR, f"incident_{idx}.json")
    with open(gt_path, "w") as f:
        json.dump(entry["gt"], f, indent=4)

    print(f"  ✅ incident_{idx}")

print(f"\n  Generated {len(DATA)} incidents (003-025).")
