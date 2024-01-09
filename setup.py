#!/usr/bin/env python3
from setuptools import setup

# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'skill-starmedia.jarbasai=skill_starmedia:StarMediaSkill'

setup(
    # this is the package name that goes on pip
    name='ovos-skill-starmedia',
    version='0.0.1',
    description='ovos V Movies skill plugin',
    url='https://github.com/JarbasSkills/skill-starmedia',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    package_dir={"skill_starmedia": ""},
    package_data={'skill_starmedia': ['locale/*', 'res/*']},
    packages=['skill_starmedia'],
    include_package_data=True,
    install_requires=["ovos_workshop~=0.0.5a1"],
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
