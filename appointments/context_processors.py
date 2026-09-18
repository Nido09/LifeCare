def cart_info(request):
    cart = request.session.get('booking_cart', [])
    return {'cart_item_count': len(cart)}