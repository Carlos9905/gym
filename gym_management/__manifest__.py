# -*- coding: utf-8 -*-
{
    "name": "GYM Management System",
    "summary": "GYM Management System",
    "version": "15.0.1.0.0",
    "description": """ 
        Control de membresias, clientes y entrenadores para un gimnasio
     """,
    "author": "José Aguilar",
    "depends": [
        "mail",
        "contacts",
        "hr",
        "product",
        "membership",
        "sale",
    ],
    "data": [
        'data/data.xml',
        "security/ir.model.access.csv",
        'views/equipments.xml',
        'views/members.xml',
        'views/membership_plan.xml',
        'views/membership.xml',
        'views/trainer_skill.xml',
        'views/trainers.xml',
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
