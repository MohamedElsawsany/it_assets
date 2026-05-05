"""
Management command: seed_data
Usage:  python manage.py seed_data
        python manage.py seed_data --clear   # wipe everything first
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed the database with realistic test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear', action='store_true',
            help='Delete all existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self._clear()

        self.stdout.write('Seeding data…')
        admin = self._get_admin()
        govs, sites        = self._seed_locations(admin)
        depts              = self._seed_departments(admin)
        employees          = self._seed_employees(admin, sites, depts)
        users              = self._seed_users(sites)
        brands, categories, models, cpus, gpus, oses, acc_types = self._seed_lookups(admin)
        devices            = self._seed_devices(admin, sites, brands, categories, models, cpus, gpus, oses)
        accessories        = self._seed_accessories(admin, sites, brands, acc_types, devices)
        self._seed_assignments(users, devices, employees)
        self._seed_transfers(users, devices, sites)
        self._seed_maintenance(users, devices)
        self.stdout.write(self.style.SUCCESS('Done! Database seeded successfully.'))

    # ──────────────────────────────────────────────────────────────────────────
    # Clear
    # ──────────────────────────────────────────────────────────────────────────
    def _clear(self):
        from maintenance.models import MaintenanceRecord, AccessoryMaintenanceRecord
        from assignments.models import DeviceAssignment, AccessoryAssignment, DeviceTransfer
        from inventory.models import Accessory, Device
        from employees.models import Employee, Department
        from locations.models import Site, Governorate
        from inventory.models import (
            Brand, DeviceCategory, DeviceModel, CPU, GPU,
            OperatingSystem, AccessoryType,
        )
        from accounts.models import User

        self.stdout.write('Clearing existing data…')
        # Delete in dependency order (children before parents)
        AccessoryMaintenanceRecord.objects.all().delete()
        MaintenanceRecord.objects.all().delete()
        AccessoryAssignment.objects.all().delete()
        DeviceAssignment.objects.all().delete()
        DeviceTransfer.objects.all().delete()
        Accessory.objects.all().delete()
        Device.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        Employee.objects.all().delete()
        Department.objects.all().delete()
        Site.objects.all().delete()
        Governorate.objects.all().delete()
        # Lookup tables: delete child lookups before Brand/Category
        DeviceModel.objects.all().delete()
        CPU.objects.all().delete()
        GPU.objects.all().delete()
        AccessoryType.objects.all().delete()
        OperatingSystem.objects.all().delete()
        Brand.objects.all().delete()
        DeviceCategory.objects.all().delete()

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _get_admin(self):
        from accounts.models import User
        return User.objects.filter(is_superuser=True).first()

    def _ago(self, days):
        return timezone.now() - timedelta(days=days)

    # ──────────────────────────────────────────────────────────────────────────
    # Locations
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_locations(self, admin):
        from locations.models import Governorate, Site

        gov_data = [
            ('Cairo',       ['Cairo HQ', 'Cairo Branch', 'New Cairo Office']),
            ('Giza',        ['Giza Main Office', 'Dokki Branch']),
            ('Alexandria',  ['Alexandria HQ', 'Alexandria Warehouse']),
            ('Aswan',       ['Aswan Office']),
            ('Luxor',       ['Luxor Branch']),
        ]

        govs, sites = [], []
        for gov_name, site_names in gov_data:
            gov, _ = Governorate.objects.get_or_create(
                name=gov_name,
                defaults={'created_by': admin},
            )
            govs.append(gov)
            for site_name in site_names:
                site, _ = Site.objects.get_or_create(
                    name=site_name,
                    defaults={'governorate': gov, 'created_by': admin},
                )
                sites.append(site)

        self.stdout.write(f'  Locations: {len(govs)} governorates, {len(sites)} sites')
        return govs, sites

    # ──────────────────────────────────────────────────────────────────────────
    # Departments
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_departments(self, admin):
        from employees.models import Department

        names = [
            'Information Technology', 'Human Resources', 'Finance',
            'Operations', 'Sales', 'Marketing', 'Customer Support',
            'Administration', 'Legal', 'Procurement',
        ]
        depts = []
        for name in names:
            dept, _ = Department.objects.get_or_create(
                name=name, defaults={'created_by': admin}
            )
            depts.append(dept)
        self.stdout.write(f'  Departments: {len(depts)}')
        return depts

    # ──────────────────────────────────────────────────────────────────────────
    # Employees
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_employees(self, admin, sites, depts):
        from employees.models import Employee

        first_names = [
            'Ahmed', 'Mohamed', 'Sara', 'Nour', 'Khaled', 'Mona', 'Omar',
            'Layla', 'Hassan', 'Fatima', 'Youssef', 'Dina', 'Tamer', 'Heba',
            'Sherif', 'Rania', 'Mahmoud', 'Aya', 'Amr', 'Noha',
        ]
        last_names = [
            'Hassan', 'Ali', 'Ibrahim', 'Mostafa', 'Sayed', 'Farouk',
            'Mansour', 'Khalil', 'Nasser', 'Hamdy', 'Rashid', 'Aziz',
        ]

        employees = []
        card_id = 100001
        for i in range(40):
            fname = first_names[i % len(first_names)]
            lname = last_names[i % len(last_names)]
            emp, created = Employee.objects.get_or_create(
                employee_card_id=card_id,
                defaults={
                    'first_name': fname,
                    'last_name': lname,
                    'department': random.choice(depts),
                    'site': random.choice(sites),
                    'created_by': admin,
                },
            )
            employees.append(emp)
            card_id += 1

        self.stdout.write(f'  Employees: {len(employees)}')
        return employees

    # ──────────────────────────────────────────────────────────────────────────
    # Users
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_users(self, sites):
        from accounts.models import User

        user_data = [
            ('it.admin',     'Ahmed',   'Nasser',  None),
            ('supervisor',   'Sara',    'Mansour', 0),
            ('inv.manager',  'Khaled',  'Ali',     1),
            ('site.mgr1',    'Mona',    'Hassan',  2),
            ('site.mgr2',    'Omar',    'Ibrahim', 3),
            ('maint.tech1',  'Youssef', 'Farouk',  4),
            ('maint.tech2',  'Dina',    'Khalil',  5),
            ('auditor',      'Layla',   'Sayed',   6),
            ('viewer',       'Tamer',   'Hamdy',   7),
        ]

        admin = User.objects.filter(is_superuser=True).first()
        users = []
        for username, fname, lname, site_idx in user_data:
            email = f'{username}@itassets.local'
            site = sites[site_idx] if site_idx is not None else None
            u, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': fname,
                    'last_name': lname,
                    'site': site,
                    'is_active': True,
                    'created_by': admin,
                },
            )
            if created:
                u.set_password('Password123!')
                u.save()
            users.append(u)

        self.stdout.write(f'  Users: {len(users)} (password: Password123!)')
        return users

    # ──────────────────────────────────────────────────────────────────────────
    # Lookup tables
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_lookups(self, admin):
        from inventory.models import (
            Brand, DeviceCategory, DeviceModel, CPU, GPU,
            OperatingSystem, AccessoryType,
        )

        # Brands
        brand_names = ['Dell', 'HP', 'Lenovo', 'Apple', 'Samsung', 'LG', 'Asus', 'Acer', 'Logitech', 'Epson']
        brands = {}
        for name in brand_names:
            b, _ = Brand.objects.get_or_create(name=name, defaults={'created_by': admin})
            brands[name] = b

        # Categories
        cat_names = ['Laptop', 'Desktop', 'Monitor', 'Printer', 'Scanner', 'UPS', 'Switch', 'Server']
        categories = {}
        for name in cat_names:
            c, _ = DeviceCategory.objects.get_or_create(name=name, defaults={'created_by': admin})
            categories[name] = c

        # Models
        model_data = [
            ('Latitude 5540',     'Dell',   'Laptop'),
            ('Latitude 3540',     'Dell',   'Laptop'),
            ('OptiPlex 7010',     'Dell',   'Desktop'),
            ('EliteBook 840 G10', 'HP',     'Laptop'),
            ('ProDesk 400 G9',    'HP',     'Desktop'),
            ('ThinkPad E14',      'Lenovo', 'Laptop'),
            ('IdeaCentre 5',      'Lenovo', 'Desktop'),
            ('MacBook Pro 14',    'Apple',  'Laptop'),
            ('UltraSharp U2422H', 'Dell',   'Monitor'),
            ('E24 G5',            'HP',     'Monitor'),
            ('27UK850-W',         'LG',     'Monitor'),
            ('LaserJet Pro 4001n','HP',     'Printer'),
            ('ECOSYS P3155dn',    'Epson',  'Printer'),
            ('WorkForce ES-500W', 'Epson',  'Scanner'),
            ('Smart-UPS 1500',    'HP',     'UPS'),
        ]
        models = {}
        for mname, bname, cname in model_data:
            m, _ = DeviceModel.objects.get_or_create(
                name=mname, brand=brands[bname],
                defaults={'category': categories[cname], 'created_by': admin},
            )
            models[mname] = m

        # CPUs
        cpu_data = [
            ('Core i5-1345U', 'Intel'),
            ('Core i7-1365U', 'Intel'),
            ('Core i5-13500', 'Intel'),
            ('Core i7-13700', 'Intel'),
            ('Ryzen 5 7530U', 'AMD'),
            ('Ryzen 7 7730U', 'AMD'),
            ('Apple M3',      'Apple'),
        ]
        intel, _ = Brand.objects.get_or_create(name='Intel', defaults={'created_by': admin})
        amd,   _ = Brand.objects.get_or_create(name='AMD',   defaults={'created_by': admin})
        cpu_brands = {'Intel': intel, 'AMD': amd, 'Apple': brands['Apple']}
        cpus = {}
        for cname, bname in cpu_data:
            c, _ = CPU.objects.get_or_create(
                name=cname, defaults={'brand': cpu_brands[bname], 'created_by': admin}
            )
            cpus[cname] = c

        # GPUs
        gpu_data = [
            ('Intel Iris Xe',    'Intel'),
            ('RTX 3050',         'NVIDIA'),
            ('Radeon RX 6600',   'AMD'),
            ('Apple M3 GPU',     'Apple'),
        ]
        nvidia, _ = Brand.objects.get_or_create(name='NVIDIA', defaults={'created_by': admin})
        gpu_brands = {'Intel': intel, 'NVIDIA': nvidia, 'AMD': amd, 'Apple': brands['Apple']}
        gpus = {}
        for gname, bname in gpu_data:
            g, _ = GPU.objects.get_or_create(
                name=gname, defaults={'brand': gpu_brands[bname], 'created_by': admin}
            )
            gpus[gname] = g

        # Operating Systems
        os_names = ['Windows 11 Pro', 'Windows 10 Pro', 'Ubuntu 22.04 LTS', 'macOS Sonoma']
        oses = {}
        for name in os_names:
            o, _ = OperatingSystem.objects.get_or_create(name=name, defaults={'created_by': admin})
            oses[name] = o

        # Accessory types
        acc_type_names = ['Mouse', 'Keyboard', 'Headset', 'Webcam', 'USB Hub', 'Laptop Bag', 'Charger', 'Docking Station']
        acc_types = {}
        for name in acc_type_names:
            a, _ = AccessoryType.objects.get_or_create(name=name, defaults={'created_by': admin})
            acc_types[name] = a

        self.stdout.write(
            f'  Lookups: {len(brands)} brands, {len(categories)} categories, '
            f'{len(models)} models, {len(cpus)} CPUs, {len(gpus)} GPUs, '
            f'{len(oses)} OS, {len(acc_types)} accessory types'
        )
        return brands, categories, models, cpus, gpus, oses, acc_types

    # ──────────────────────────────────────────────────────────────────────────
    # Devices
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_devices(self, admin, sites, brands, categories, models, cpus, gpus, oses):
        from inventory.models import Device, DeviceFlag

        laptop_models  = ['Latitude 5540', 'Latitude 3540', 'EliteBook 840 G10', 'ThinkPad E14', 'MacBook Pro 14']
        desktop_models = ['OptiPlex 7010', 'ProDesk 400 G9', 'IdeaCentre 5']
        monitor_models = ['UltraSharp U2422H', 'E24 G5', '27UK850-W']
        printer_models = ['LaserJet Pro 4001n', 'ECOSYS P3155dn']
        other_models   = ['WorkForce ES-500W', 'Smart-UPS 1500']

        cpu_list = list(cpus.values())
        gpu_list = list(gpus.values())
        os_list  = list(oses.values())
        flags    = [DeviceFlag.AVAILABLE] * 5 + [DeviceFlag.ASSIGNED] * 3 + [DeviceFlag.RETIRED] + [DeviceFlag.LOST]

        devices = []
        serial_counter = 1000

        device_configs = (
            [(m, 8, 256, 'laptop') for m in laptop_models * 5] +
            [(m, 16, 512, 'desktop') for m in desktop_models * 4] +
            [(m, None, None, 'monitor') for m in monitor_models * 3] +
            [(m, None, None, 'printer') for m in printer_models * 2] +
            [(m, None, None, 'other') for m in other_models]
        )

        for model_name, ram, ssd, dtype in device_configs:
            serial = f'SN-{serial_counter:05d}'
            serial_counter += 1
            dm = models[model_name]

            kwargs = {
                'category':    dm.category,
                'brand':       dm.brand,
                'device_model': dm,
                'site':        random.choice(sites),
                'flag':        random.choice(flags),
                'created_by':  admin,
            }

            if dtype in ('laptop', 'desktop'):
                kwargs.update({
                    'cpu':              random.choice(cpu_list),
                    'gpu':              random.choice(gpu_list),
                    'ram_size_gb':      ram,
                    'ssd_storage_gb':   ssd,
                    'hdd_storage_gb':   500 if dtype == 'desktop' else None,
                    'operating_system': random.choice(os_list),
                })
            elif dtype == 'monitor':
                kwargs['screen_size_inch'] = random.choice([24.0, 27.0, 32.0])

            dev, created = Device.objects.get_or_create(serial_number=serial, defaults=kwargs)
            if created:
                devices.append(dev)

        self.stdout.write(f'  Devices: {len(devices)}')
        return devices

    # ──────────────────────────────────────────────────────────────────────────
    # Accessories
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_accessories(self, admin, sites, brands, acc_types, devices):
        from inventory.models import Accessory, DeviceFlag

        brand_list = [brands[b] for b in ['Dell', 'HP', 'Lenovo', 'Logitech'] if b in brands]
        type_list  = list(acc_types.values())
        accessories = []

        for i in range(50):
            serial = f'ACC-{i+1:04d}'
            atype  = type_list[i % len(type_list)]
            device = devices[i % len(devices)] if i < 30 else None
            site   = device.site if device else random.choice(sites)

            acc, created = Accessory.objects.get_or_create(
                serial_number=serial,
                defaults={
                    'accessory_type': atype,
                    'brand':          random.choice(brand_list),
                    'device':         device,
                    'site':           site,
                    'flag':           DeviceFlag.AVAILABLE if not device else DeviceFlag.ASSIGNED,
                    'created_by':     admin,
                },
            )
            if created:
                accessories.append(acc)

        self.stdout.write(f'  Accessories: {len(accessories)}')
        return accessories

    # ──────────────────────────────────────────────────────────────────────────
    # Assignments
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_assignments(self, users, devices, employees):
        from assignments.models import DeviceAssignment
        from inventory.models import DeviceFlag

        assigner = users[0]  # IT admin
        count = 0

        # 20 active assignments
        available_devices = [d for d in devices if d.flag == DeviceFlag.AVAILABLE][:20]
        for i, dev in enumerate(available_devices):
            emp = employees[i % len(employees)]
            assigned_date = self._ago(random.randint(10, 300))
            if not DeviceAssignment.objects.filter(device=dev, returned_date__isnull=True).exists():
                DeviceAssignment.objects.create(
                    device=dev,
                    employee=emp,
                    assigned_date=assigned_date,
                    notes=f'Assigned for {emp.department.name} work',
                    assigned_by=assigner,
                )
            dev.flag = DeviceFlag.ASSIGNED
            dev.save(update_fields=['flag'])
            count += 1

        # 10 returned (historical) assignments
        other_devices = [d for d in devices if d.flag not in (DeviceFlag.ASSIGNED,)][:10]
        for i, dev in enumerate(other_devices):
            emp = employees[(i + 5) % len(employees)]
            assigned_date = self._ago(random.randint(200, 500))
            returned_date = assigned_date + timedelta(days=random.randint(30, 180))
            DeviceAssignment.objects.create(
                device=dev,
                employee=emp,
                assigned_date=assigned_date,
                returned_date=returned_date,
                notes='Returned after project completion',
                assigned_by=assigner,
            )
            count += 1

        self.stdout.write(f'  Assignments: {count}')

    # ──────────────────────────────────────────────────────────────────────────
    # Transfers
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_transfers(self, users, devices, sites):
        from assignments.models import DeviceTransfer

        transferrer = users[0]
        count = 0

        transfer_devices = devices[:15]
        for i, dev in enumerate(transfer_devices):
            from_site = sites[i % len(sites)]
            to_site   = sites[(i + 1) % len(sites)]
            if from_site == to_site:
                to_site = sites[(i + 2) % len(sites)]

            DeviceTransfer.objects.create(
                device=dev,
                from_site=from_site,
                to_site=to_site,
                transfer_date=self._ago(random.randint(5, 180)),
                notes=f'Relocated to {to_site.name}',
                transferred_by=transferrer,
            )
            count += 1

        self.stdout.write(f'  Transfers: {count}')

    # ──────────────────────────────────────────────────────────────────────────
    # Maintenance
    # ──────────────────────────────────────────────────────────────────────────
    def _seed_maintenance(self, users, devices):
        from maintenance.models import MaintenanceRecord
        from inventory.models import DeviceFlag

        tech = users[5]  # maint.tech1

        maint_types   = ['Internal', 'External', 'Internal', 'External', 'Internal']
        vendors       = ['TechFix Egypt', 'IT Solutions Co.', 'Cairo Repair Center', None]
        issues        = [
            'Screen flickering intermittently',
            'Battery not charging properly',
            'Fan making loud noise',
            'Keyboard keys not responding',
            'System overheating',
            'Hard drive failure',
            'RAM upgrade requested',
            'Annual hardware inspection',
            'OS reinstallation needed',
            'Network card malfunction',
        ]

        count = 0
        maint_devices = [d for d in devices if d.flag not in (DeviceFlag.ASSIGNED,)][:20]

        for i, dev in enumerate(maint_devices):
            sent_date    = self._ago(random.randint(30, 200))
            is_closed    = (i % 4 != 0)  # ~75% closed
            returned_date = (sent_date + timedelta(days=random.randint(3, 21))) if is_closed else None

            prev_flag = dev.flag
            mtype = maint_types[i % len(maint_types)]
            rec = MaintenanceRecord(
                device=dev,
                maintenance_type=mtype,
                vendor_name=vendors[i % len(vendors)] if mtype == 'External' else None,
                sent_date=sent_date,
                returned_date=returned_date,
                issue_description=issues[i % len(issues)],
                resolution_notes='Issue resolved and device tested.' if is_closed else '',
                cost=random.choice([None, 150, 300, 500, 750, 1200]),
                created_by=tech,
                previous_flag=prev_flag,
            )
            rec.save()

            if not is_closed:
                dev.flag = DeviceFlag.UNDER_MAINTENANCE
                dev.maintenance_mode = True
                dev.save(update_fields=['flag', 'maintenance_mode'])

            count += 1

        self.stdout.write(f'  Maintenance records: {count}')
