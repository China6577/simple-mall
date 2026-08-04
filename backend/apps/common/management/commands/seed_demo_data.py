"""
生成教学演示用的模拟数据。

用法：
    python manage.py seed_demo_data [--clean]

--clean 会先清空本命令生成的业务数据（保留用户表中的管理员），再重新创建。
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.carts.models import CartItem
from apps.coupons.models import Coupon, UserCoupon
from apps.inventory.models import Stock
from apps.orders.models import Order, OrderItem
from apps.products.models import Brand, Category, SPU, SKU

User = get_user_model()


class Command(BaseCommand):
    help = "为 SimpleMall 生成教学演示数据"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="清空已存在的演示数据后重新生成",
        )

    def handle(self, *args, **options):
        clean = options["clean"]

        if clean:
            self._clean_demo_data()
            self.stdout.write(self.style.WARNING("已清空旧演示数据"))

        with transaction.atomic():
            admin, users = self._create_users()
            categories = self._create_categories()
            brands = self._create_brands()
            spus, skus = self._create_products(categories, brands)
            coupons = self._create_coupons()
            self._create_user_coupons(users, coupons)
            self._create_cart_items(users, skus)
            self._create_orders(users, skus)

        self.stdout.write(self.style.SUCCESS("演示数据生成完成"))
        self.stdout.write("管理员账号：admin@mall.local / 123456")
        self.stdout.write("普通用户：user1@mall.local / user123456")
        self.stdout.write("          user2@mall.local / user123456")

    def _clean_demo_data(self):
        """不再清理任何数据；保留所有用户账号与业务数据。"""
        self.stdout.write(self.style.WARNING("--clean 已禁用，不会清理任何数据"))

    def _create_users(self):
        """创建管理员与演示用户。"""
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@mall.local",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.set_password("123456")
        admin.save()

        users = []
        avatars = [
            "avatars/Friendly_young_Asian_male_user_2026-08-02T10-56-02.png",
            "avatars/Friendly_young_Asian_female_us_2026-08-02T10-56-02.png",
        ]
        for idx in range(1, 3):
            user, _ = User.objects.get_or_create(
                username=f"user{idx}",
                defaults={
                    "email": f"user{idx}@mall.local",
                    "role": User.Role.CONSUMER,
                },
            )
            # 强制更新头像路径，确保重新 seed 时能同步新图片
            user.avatar = avatars[idx - 1]
            user.set_password("user123456")
            user.save()
            users.append(user)

        return admin, users

    def _create_categories(self):
        """创建商品分类。"""
        data = [
            {"name": "手机通讯", "level": 1, "sort_order": 1},
            {"name": "电脑办公", "level": 1, "sort_order": 2},
            {"name": "智能穿戴", "level": 1, "sort_order": 3},
            {"name": "数码配件", "level": 1, "sort_order": 4},
        ]
        categories = []
        for item in data:
            cat, _ = Category.objects.get_or_create(name=item["name"], defaults=item)
            categories.append(cat)
        return categories

    def _create_brands(self):
        """创建品牌。"""
        data = [
            {"name": "TechPro"},
            {"name": "BlueSky"},
            {"name": "GreenLife"},
        ]
        brands = []
        for item in data:
            brand, _ = Brand.objects.get_or_create(name=item["name"], defaults=item)
            brands.append(brand)
        return brands

    def _create_products(self, categories, brands):
        """创建 SPU 与 SKU，并关联生成的商品主图。"""
        products = [
            {
                "spu_code": "SPU-PHONE-001",
                "name": "TechPro X1 智能手机",
                "category": categories[0],
                "brand": brands[0],
                "description": "旗舰性能，120Hz 高刷屏幕，适合教学演示。",
                "main_image": "products/spu/TechPro_X1_flagship_smartphone_2026-08-02T10-55-25.png",
                "skus": [
                    {"sku_code": "SKU-PHONE-001-BLK", "specs": {"颜色": "曜石黑", "内存": "128GB"}, "price": "3999.00", "stock": 100},
                    {"sku_code": "SKU-PHONE-001-WHT", "specs": {"颜色": "珍珠白", "内存": "256GB"}, "price": "4499.00", "stock": 80},
                ],
            },
            {
                "spu_code": "SPU-LAPTOP-001",
                "name": "BlueBook Pro 14 笔记本",
                "category": categories[1],
                "brand": brands[1],
                "description": "轻薄办公本，2.5K 屏幕，演示库存与订单流程。",
                "main_image": "products/spu/BlueBook_Pro_14_silver_ultrabo_2026-08-02T10-55-25.png",
                "skus": [
                    {"sku_code": "SKU-LAPTOP-001-SIL", "specs": {"颜色": "银色", "配置": "16G+512G"}, "price": "5999.00", "stock": 50},
                    {"sku_code": "SKU-LAPTOP-001-GRY", "specs": {"颜色": "深空灰", "配置": "32G+1T"}, "price": "7999.00", "stock": 30},
                ],
            },
            {
                "spu_code": "SPU-WATCH-001",
                "name": "GreenLife 智能手表",
                "category": categories[2],
                "brand": brands[2],
                "description": "健康监测，7 天续航，演示优惠券叠加。",
                "main_image": "products/spu/GreenLife_smart_watch__black_c_2026-08-02T10-55-26.png",
                "skus": [
                    {"sku_code": "SKU-WATCH-001-BLK", "specs": {"颜色": "黑色", "表带": "硅胶"}, "price": "1299.00", "stock": 200},
                ],
            },
            {
                "spu_code": "SPU-EARPHONE-001",
                "name": "BlueSky 真无线耳机",
                "category": categories[3],
                "brand": brands[1],
                "description": "主动降噪，30 小时续航，沉浸式音质体验。",
                "main_image": "products/spu/BlueSky_true_wireless_earbuds__2026-08-02T10-55-25.png",
                "skus": [
                    {"sku_code": "SKU-EARPHONE-001-WHT", "specs": {"颜色": "白色"}, "price": "699.00", "stock": 150},
                    {"sku_code": "SKU-EARPHONE-001-BLK", "specs": {"颜色": "黑色"}, "price": "699.00", "stock": 150},
                ],
            },
            {
                "spu_code": "SPU-TABLET-001",
                "name": "TechPro Pad 平板电脑",
                "category": categories[1],
                "brand": brands[0],
                "description": "11 英寸高清屏幕，轻薄便携，办公娱乐两不误。",
                "main_image": "products/spu/TechPro_Pad_tablet_computer__1_2026-08-02T10-55-25.png",
                "skus": [
                    {"sku_code": "SKU-TABLET-001-GRY", "specs": {"颜色": "深空灰", "内存": "128GB"}, "price": "3299.00", "stock": 60},
                    {"sku_code": "SKU-TABLET-001-SLV", "specs": {"颜色": "银色", "内存": "256GB"}, "price": "3999.00", "stock": 50},
                ],
            },
            {
                "spu_code": "SPU-BAND-001",
                "name": "GreenLife 运动手环",
                "category": categories[2],
                "brand": brands[2],
                "description": "全天候健康监测，14 天超长续航，运动好伴侣。",
                "main_image": "products/spu/GreenLife_fitness_band__lightw_2026-08-02T10-56-02.png",
                "skus": [
                    {"sku_code": "SKU-BAND-001-BLK", "specs": {"颜色": "黑色"}, "price": "299.00", "stock": 300},
                ],
            },
            {
                "spu_code": "SPU-CHARGER-001",
                "name": "TechPro 无线充电器",
                "category": categories[3],
                "brand": brands[0],
                "description": "15W 快充，智能温控，兼容多种设备。",
                "main_image": "products/spu/TechPro_wireless_charging_pad__2026-08-02T10-56-02.png",
                "skus": [
                    {"sku_code": "SKU-CHARGER-001-BLK", "specs": {"颜色": "黑色"}, "price": "199.00", "stock": 500},
                ],
            },
            {
                "spu_code": "SPU-KEYBOARD-001",
                "name": "BlueSky 机械键盘",
                "category": categories[1],
                "brand": brands[1],
                "description": "RGB 背光，青轴手感，电竞办公两相宜。",
                "main_image": "products/spu/BlueSky_mechanical_keyboard__R_2026-08-02T10-56-02.png",
                "skus": [
                    {"sku_code": "SKU-KEYBOARD-001-BLK", "specs": {"颜色": "黑色", "轴体": "青轴"}, "price": "499.00", "stock": 120},
                    {"sku_code": "SKU-KEYBOARD-001-WHT", "specs": {"颜色": "白色", "轴体": "红轴"}, "price": "549.00", "stock": 100},
                ],
            },
            {
                "spu_code": "SPU-FOLD-PHONE-001",
                "name": "TechPro Fold Z 折叠手机",
                "category": categories[0],
                "brand": brands[0],
                "description": "创新折叠屏设计，展开即是平板，商务娱乐兼顾。",
                "main_image": "products/spu/TechPro_Fold_Z_foldable_smartp_2026-08-02T12-11-11.png",
                "skus": [
                    {"sku_code": "SKU-FOLD-PHONE-001-BLK", "specs": {"颜色": "曜石黑", "内存": "512GB"}, "price": "8999.00", "stock": 40},
                ],
            },
            {
                "spu_code": "SPU-GAME-PHONE-001",
                "name": "BlueSky 游戏手机",
                "category": categories[0],
                "brand": brands[1],
                "description": "电竞级散热，165Hz 高刷屏，为游戏而生。",
                "main_image": "products/spu/BlueSky_gaming_smartphone__agg_2026-08-02T12-11-45.png",
                "skus": [
                    {"sku_code": "SKU-GAME-PHONE-001-BLK", "specs": {"颜色": "暗夜黑", "内存": "256GB"}, "price": "4999.00", "stock": 60},
                ],
            },
            {
                "spu_code": "SPU-AIRBOOK-001",
                "name": "TechPro AirBook 轻薄本",
                "category": categories[1],
                "brand": brands[0],
                "description": "980g 超轻机身，14 小时续航，移动办公首选。",
                "main_image": "products/spu/TechPro_AirBook_ultra_thin_sil_2026-08-02T12-12-19.png",
                "skus": [
                    {"sku_code": "SKU-AIRBOOK-001-SLV", "specs": {"颜色": "月光银", "配置": "16G+512G"}, "price": "6999.00", "stock": 45},
                ],
            },
            {
                "spu_code": "SPU-AIO-001",
                "name": "GreenLife 一体机",
                "category": categories[1],
                "brand": brands[2],
                "description": "23.8 英寸高清大屏，极简桌面，家庭办公一站搞定。",
                "main_image": "products/spu/GreenLife_all_in_one_desktop_c_2026-08-02T12-12-19.png",
                "skus": [
                    {"sku_code": "SKU-AIO-001-WHT", "specs": {"颜色": "白色", "配置": "8G+256G"}, "price": "3999.00", "stock": 35},
                ],
            },
            {
                "spu_code": "SPU-MONITOR-001",
                "name": "BlueSky 27 英寸 4K 显示器",
                "category": categories[1],
                "brand": brands[1],
                "description": "4K 超清分辨率，99% sRGB 色域，设计师之选。",
                "main_image": "products/spu/BlueSky_27_inch_4K_monitor__th_2026-08-02T12-12-19.png",
                "skus": [
                    {"sku_code": "SKU-MONITOR-001-SLV", "specs": {"颜色": "银色", "尺寸": "27英寸"}, "price": "2499.00", "stock": 55},
                ],
            },
            {
                "spu_code": "SPU-BAND-PRO-001",
                "name": "TechPro Smart Band Pro",
                "category": categories[2],
                "brand": brands[0],
                "description": "曲面 AMOLED 大屏，血氧心率监测，专业运动指导。",
                "main_image": "products/spu/TechPro_Smart_Band_Pro_fitness_2026-08-02T12-12-19.png",
                "skus": [
                    {"sku_code": "SKU-BAND-PRO-001-BLK", "specs": {"颜色": "黑色"}, "price": "599.00", "stock": 250},
                ],
            },
            {
                "spu_code": "SPU-GLASSES-001",
                "name": "BlueSky 智能眼镜",
                "category": categories[2],
                "brand": brands[1],
                "description": "轻量镜架，AR 信息投射，开放式定向音频。",
                "main_image": "products/spu/BlueSky_smart_glasses__lightwe_2026-08-02T12-12-55.png",
                "skus": [
                    {"sku_code": "SKU-GLASSES-001-BLK", "specs": {"颜色": "黑色"}, "price": "1999.00", "stock": 70},
                ],
            },
            {
                "spu_code": "SPU-KIDS-WATCH-001",
                "name": "GreenLife 儿童手表",
                "category": categories[2],
                "brand": brands[2],
                "description": "GPS 定位，4G 通话，安全围栏，守护孩子成长。",
                "main_image": "products/spu/GreenLife_kids_smartwatch__col_2026-08-02T12-12-55.png",
                "skus": [
                    {"sku_code": "SKU-KIDS-WATCH-001-PNK", "specs": {"颜色": "粉色"}, "price": "699.00", "stock": 180},
                ],
            },
            {
                "spu_code": "SPU-POWERBANK-001",
                "name": "TechPro 20000mAh 移动电源",
                "category": categories[3],
                "brand": brands[0],
                "description": "大容量快充，数显电量，多设备同时充电。",
                "main_image": "products/spu/TechPro_20000mAh_power_bank__s_2026-08-02T12-12-55.png",
                "skus": [
                    {"sku_code": "SKU-POWERBANK-001-BLK", "specs": {"颜色": "黑色"}, "price": "299.00", "stock": 400},
                ],
            },
            {
                "spu_code": "SPU-CASE-SET-001",
                "name": "BlueSky 手机壳套装",
                "category": categories[3],
                "brand": brands[1],
                "description": "防摔透明壳 + 磨砂壳组合，还原裸机手感。",
                "main_image": "products/spu/BlueSky_premium_phone_case_set_2026-08-02T12-12-55.png",
                "skus": [
                    {"sku_code": "SKU-CASE-SET-001-CLR", "specs": {"颜色": "透明"}, "price": "99.00", "stock": 600},
                ],
            },
            {
                "spu_code": "SPU-CABLE-SET-001",
                "name": "TechPro USB-C 数据线套装",
                "category": categories[3],
                "brand": brands[0],
                "description": "编织尼龙线身，三口组合，快充不伤机。",
                "main_image": "products/spu/TechPro_USB_C_cable_set__braid_2026-08-02T12-13-27.png",
                "skus": [
                    {"sku_code": "SKU-CABLE-SET-001-WHT", "specs": {"颜色": "白色"}, "price": "79.00", "stock": 800},
                ],
            },
            {
                "spu_code": "SPU-SPEAKER-001",
                "name": "BlueSky 便携蓝牙音箱",
                "category": categories[3],
                "brand": brands[1],
                "description": "360° 环绕音效，IPX7 防水，户外随行。",
                "main_image": "products/spu/BlueSky_portable_bluetooth_spe_2026-08-02T12-13-27.png",
                "skus": [
                    {"sku_code": "SKU-SPEAKER-001-BLK", "specs": {"颜色": "黑色"}, "price": "349.00", "stock": 300},
                ],
            },
        ]

        spus = []
        skus = []
        for idx, product in enumerate(products):
            spu, _ = SPU.objects.get_or_create(
                spu_code=product["spu_code"],
                defaults={
                    "name": product["name"],
                    "category": product["category"],
                    "brand": product["brand"],
                    "description": product["description"],
                    "is_active": True,
                },
            )
            # 强制更新主图路径，确保重新 seed 时能同步新图片
            spu.main_image = product["main_image"]
            spu.save(update_fields=["main_image"])
            spus.append(spu)

            for sku_index, sku_data in enumerate(product["skus"]):
                sku, _ = SKU.objects.get_or_create(
                    sku_code=sku_data["sku_code"],
                    defaults={
                        "spu": spu,
                        "price": sku_data["price"],
                        "cost_price": Decimal(sku_data["price"]) * Decimal("0.7"),
                        "stock": sku_data["stock"],
                        "sales": 0,
                        "status": True,
                        "is_default": sku_index == 0,
                        "specs": sku_data["specs"],
                    },
                )
                skus.append(sku)
                # 库存记录由信号自动创建，这里显式确保数值正确
                stock, _ = Stock.objects.get_or_create(sku=sku, defaults={"quantity": sku_data["stock"]})
                stock.quantity = sku_data["stock"]
                stock.save(update_fields=["quantity"])

        return spus, skus

    def _create_coupons(self):
        """创建优惠券模板：满减券 + 折扣券。"""
        now = timezone.now()
        data = [
            {
                "code": "NEW-USER-10",
                "name": "新用户满100减10",
                "type": Coupon.Type.FIXED_AMOUNT,
                "value": "10.00",
                "min_order_amount": "100.00",
                "total_quantity": 1000,
                "remaining_quantity": 1000,
                "limit_per_user": 1,
                "start_time": now,
                "end_time": now + timezone.timedelta(days=30),
            },
            {
                "code": "SAVE-50",
                "name": "满500减50",
                "type": Coupon.Type.FIXED_AMOUNT,
                "value": "50.00",
                "min_order_amount": "500.00",
                "total_quantity": 500,
                "remaining_quantity": 500,
                "limit_per_user": 1,
                "start_time": now,
                "end_time": now + timezone.timedelta(days=30),
            },
            {
                "code": "DISCOUNT-9",
                "name": "9折通用券（最高减100）",
                "type": Coupon.Type.PERCENTAGE,
                "value": "0.90",
                "min_order_amount": "0.00",
                "max_discount_amount": "100.00",
                "total_quantity": 300,
                "remaining_quantity": 300,
                "limit_per_user": 1,
                "start_time": now,
                "end_time": now + timezone.timedelta(days=30),
            },
        ]
        coupons = []
        for item in data:
            coupon, _ = Coupon.objects.get_or_create(code=item["code"], defaults=item)
            coupons.append(coupon)
        return coupons

    def _create_user_coupons(self, users, coupons):
        """为演示用户领取优惠券。"""
        for user in users:
            for coupon in coupons:
                UserCoupon.objects.get_or_create(
                    user=user,
                    coupon=coupon,
                    defaults={"status": UserCoupon.Status.UNUSED},
                )

    def _create_cart_items(self, users, skus):
        """为演示用户添加购物车条目。"""
        cart_data = [
            (users[0], skus[0], 1, True),   # user1 加购手机黑色
            (users[0], skus[2], 1, False),  # user1 加购笔记本银色，未选中
            (users[1], skus[4], 2, True),   # user2 加购手表
        ]
        for user, sku, quantity, selected in cart_data:
            CartItem.objects.get_or_create(
                user=user,
                sku=sku,
                defaults={"quantity": quantity, "selected": selected},
            )

    def _create_orders(self, users, skus):
        """创建历史订单，展示不同状态。"""
        orders = [
            {
                "user": users[0],
                "status": Order.Status.PAID,
                "sku": skus[1],  # 白色手机
                "quantity": 1,
                "address_snapshot": {
                    "receiver": "张三",
                    "phone": "13800138000",
                    "province": "广东省",
                    "city": "深圳市",
                    "district": "南山区",
                    "detail": "科技园 demo 地址",
                },
            },
            {
                "user": users[1],
                "status": Order.Status.PENDING_PAYMENT,
                "sku": skus[3],  # 高配笔记本
                "quantity": 1,
                "address_snapshot": {
                    "receiver": "李四",
                    "phone": "13900139000",
                    "province": "浙江省",
                    "city": "杭州市",
                    "district": "余杭区",
                    "detail": "未来科技城 demo 地址",
                },
            },
        ]

        for order_data in orders:
            sku = order_data["sku"]
            quantity = order_data["quantity"]
            total = sku.price * quantity

            order, _ = Order.objects.get_or_create(
                order_no=f"DEMO-{order_data['user'].id}-{sku.id}",
                defaults={
                    "user": order_data["user"],
                    "status": order_data["status"],
                    "total_amount": total,
                    "freight_amount": Decimal("0"),
                    "payable_amount": total,
                    "discount_amount": Decimal("0"),
                    "address_snapshot": order_data["address_snapshot"],
                    "remark": "演示订单",
                },
            )
            OrderItem.objects.get_or_create(
                order=order,
                sku=sku,
                defaults={
                    "sku_code": sku.sku_code,
                    "spu_name": sku.spu.name,
                    "specs": sku.specs,
                    "main_image": "",
                    "price": sku.price,
                    "quantity": quantity,
                    "subtotal": total,
                },
            )
