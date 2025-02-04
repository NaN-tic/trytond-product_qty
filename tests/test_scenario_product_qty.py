import unittest
import datetime
from decimal import Decimal
from proteus import Model
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules
from trytond.modules.stock.exceptions import MoveFutureWarning


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install product_qty
        config = activate_modules(['product_qty'])

        Warning = Model.get('res.user.warning')

        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)

        # Create company
        _ = create_company()
        company = get_company()

        # Create parties
        Party = Model.get('party.party')
        supplier = Party(name='Supplier')
        supplier.save()
        customer = Party(name='Customer')
        customer.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])

        Product = Model.get('product.product')
        ProductTemplate = Model.get('product.template')
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'goods'
        template.list_price = Decimal('10')
        template.cost_price_method = 'fixed'
        product, = template.products
        product.cost_price = Decimal('5')
        template.save()
        product, = template.products

        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'goods'
        template.list_price = Decimal('10')
        template.cost_price_method = 'fixed'
        product2, = template.products
        product2.cost_price = Decimal('5')
        template.save()
        product2, = template.products

        Location = Model.get('stock.location')
        storage, = Location.find([
            ('code', '=', 'STO'),
            ])
        supplier_loc, = Location.find([
            ('code', '=', 'SUP'),
            ])
        customer_loc, = Location.find([
            ('code', '=', 'CUS'),
            ])
        # Create an Inventory
        Inventory = Model.get('stock.inventory')
        inventory = Inventory()
        inventory.location = storage
        inventory_line = inventory.lines.new(product=product)
        inventory_line.quantity = 100.0
        inventory_line.expected_quantity = 0.0
        inventory.click('confirm')
        self.assertEqual(inventory.state, 'done')

        Move = Model.get('stock.move')
        move = Move(
            from_location=supplier_loc,
            to_location=storage,
            product=product,
            unit=product.default_uom,
            unit_price=Decimal(10),
            currency=company.currency,
            quantity=50.0,
            planned_date=tomorrow,
            effective_date=tomorrow,
            )
        move.save()
        with self.assertRaises(MoveFutureWarning):
            try:
                move.click('do')
            except MoveFutureWarning as warning:
                _, (key, *_) = warning.args
                raise
        Warning(user=config.user, name=key).save()
        move.click('do')

        self.assertEqual(product.quantity, 100.0)
        self.assertEqual(product.forecast_quantity, 150.0)

        self.assertEqual(product2.quantity, 0.0)
        self.assertEqual(product2.forecast_quantity, 0.0)

        self.assertEqual(len(Product.find([('quantity', '=', 100)])), 1)

        # Search where qty is 0, has not products because in case product
        # has not moves, not return those products
        self.assertEqual(len(Product.find([('quantity', '=', 0)])), 0)

        # Now, in product2 add incoming move, and after, outgoing move
        move = Move(
            from_location=supplier_loc,
            to_location=storage,
            product=product2,
            unit=product.default_uom,
            unit_price=Decimal(10),
            currency=company.currency,
            quantity=100.0,
            )
        move.save()
        move.click('do')

        # Qty product and product2 are 100
        self.assertEqual(len(Product.find([('quantity', '=', 100)])), 2)

        move = Move(
            from_location=storage,
            to_location=customer_loc,
            product=product2,
            unit=product.default_uom,
            unit_price=Decimal(10),
            currency=company.currency,
            quantity=100.0,
            )
        move.save()
        move.click('do')

        # Qty product is 100, but product2 now is 0

        # Search product that qty is 100
        qty_100, = Product.find([('quantity', '=', 100)])
        self.assertEqual(qty_100, product)

        # Search product that qty is 0
        qty_0, = Product.find([('quantity', '=', 0)])
        self.assertEqual(qty_0, product2)
