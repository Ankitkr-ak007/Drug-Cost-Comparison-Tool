import reflex as rx
from reflex_enterprise.components.map.types import LatLng, latlng
import httpx
import asyncio
import math
import logging


class CheckoutState(rx.State):
    house_no: str = ""
    area: str = ""
    landmark: str = ""
    pincode: str = ""
    address_error: str = ""
    is_geocoding: bool = False
    geocode_status: str = ""
    shop_lat: float = 22.8046
    shop_lng: float = 86.2029
    shop_name: str = "MediSmart Pharmacy, Bistupur"
    shop_address: str = "Main Road, Bistupur, Jamshedpur, Jharkhand 831001"
    user_lat: float = 0.0
    user_lng: float = 0.0
    user_address_resolved: str = ""
    has_user_location: bool = False
    map_center: LatLng = latlng(lat=22.8046, lng=86.2029)
    map_zoom: float = 13.0
    route_positions: list[LatLng] = []
    order_submitted: bool = False
    order_loading: bool = False
    saved_order: dict = {}
    cart_items: list[dict] = [
        {"name": "Paracetamol 500mg (Generic)", "qty": 2, "price": 8.0},
        {"name": "Pantoprazole 40mg (Generic)", "qty": 1, "price": 18.0},
        {"name": "Metformin 500mg (Generic)", "qty": 1, "price": 10.0},
    ]
    is_gps_loading: bool = False

    @rx.var
    def cart_total(self) -> float:
        return sum((item["price"] * item["qty"] for item in self.cart_items))

    @rx.var
    def cart_item_count(self) -> int:
        return sum((item["qty"] for item in self.cart_items))

    @rx.var
    def full_address(self) -> str:
        parts = [self.house_no, self.area, self.landmark, self.pincode]
        return ", ".join((p for p in parts if p.strip()))

    @rx.var
    def delivery_distance_km(self) -> float:
        if not self.has_user_location:
            return 0.0
        R = 6371.0
        dlat = math.radians(self.user_lat - self.shop_lat)
        dlon = math.radians(self.user_lng - self.shop_lng)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(self.shop_lat))
            * math.cos(math.radians(self.user_lat))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)

    @rx.var
    def estimated_delivery_time(self) -> str:
        d = self.delivery_distance_km
        if d == 0:
            return "—"
        mins = max(15, int(d * 3))
        if mins >= 60:
            return f"{mins // 60}h {mins % 60}min"
        return f"{mins} min"

    def _generate_route_points(self):
        """Generate intermediate points between shop and user for a polyline route."""
        if not self.has_user_location:
            self.route_positions = []
            return
        num_points = 8
        points = []
        for i in range(num_points + 1):
            t = i / num_points
            lat = self.shop_lat + t * (self.user_lat - self.shop_lat)
            lng = self.shop_lng + t * (self.user_lng - self.shop_lng)
            if 0 < t < 1:
                offset = math.sin(t * math.pi) * 0.003
                lat += offset
            points.append(latlng(lat=lat, lng=lng))
        self.route_positions = points

    @rx.event(background=True)
    async def geocode_address(self, form_data: dict):
        """Geocode the address using Nominatim and update map."""
        async with self:
            self.house_no = form_data.get("house_no", "").strip()
            self.area = form_data.get("area", "").strip()
            self.landmark = form_data.get("landmark", "").strip()
            self.pincode = form_data.get("pincode", "").strip()
            self.address_error = ""
            if not self.area:
                self.address_error = "Area/Street is required"
                return
            if (
                not self.pincode
                or len(self.pincode) != 6
                or (not self.pincode.isdigit())
            ):
                self.address_error = "Valid 6-digit pincode is required"
                return
            self.is_geocoding = True
            self.geocode_status = "Locating your address..."
        try:
            query_parts = [
                self.house_no,
                self.area,
                self.landmark,
                self.pincode,
                "Jamshedpur",
                "India",
            ]
            query = ", ".join((p for p in query_parts if p))
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": query, "format": "json", "limit": 1},
                    headers={"User-Agent": "MediSmart/1.0"},
                    timeout=10.0,
                )
                resp.raise_for_status()
                data = resp.json()
                if not data:
                    resp2 = await client.get(
                        "https://nominatim.openstreetmap.org/search",
                        params={
                            "q": f"{self.area}, {self.pincode}, Jamshedpur, India",
                            "format": "json",
                            "limit": 1,
                        },
                        headers={"User-Agent": "MediSmart/1.0"},
                        timeout=10.0,
                    )
                    data = resp2.json()
                if data:
                    lat = float(data[0]["lat"])
                    lng = float(data[0]["lon"])
                    display = data[0].get("display_name", self.full_address)
                    async with self:
                        self.user_lat = lat
                        self.user_lng = lng
                        self.user_address_resolved = display
                        self.has_user_location = True
                        center_lat = (self.shop_lat + lat) / 2
                        center_lng = (self.shop_lng + lng) / 2
                        self.map_center = latlng(lat=center_lat, lng=center_lng)
                        dist = self.delivery_distance_km
                        if dist < 2:
                            self.map_zoom = 14.0
                        elif dist < 5:
                            self.map_zoom = 13.0
                        elif dist < 15:
                            self.map_zoom = 12.0
                        elif dist < 50:
                            self.map_zoom = 10.0
                        else:
                            self.map_zoom = 8.0
                        self._generate_route_points()
                        self.is_geocoding = False
                        self.geocode_status = ""
                else:
                    async with self:
                        self.address_error = "Could not locate this address. Please check the details or use GPS."
                        self.is_geocoding = False
                        self.geocode_status = ""
        except Exception as e:
            logging.exception(f"Geocoding error: {e}")
            async with self:
                self.address_error = (
                    "Network error while locating address. Please try again."
                )
                self.is_geocoding = False
                self.geocode_status = ""

    @rx.event
    def use_gps_location(self):
        """Trigger browser geolocation."""
        self.is_gps_loading = True
        self.address_error = ""
        self.geocode_status = "Getting your GPS location..."
        return rx.call_script(
            """
            return new Promise((resolve) => {
                navigator.geolocation.getCurrentPosition(
                    (pos) => resolve([pos.coords.latitude, pos.coords.longitude]),
                    (err) => {
                        let msg = "Location unavailable";
                        if (err.code === 1) msg = "Permission denied";
                        else if (err.code === 3) msg = "Timed out";
                        resolve(["error", msg]);
                    },
                    {enableHighAccuracy: true, timeout: 10000}
                );
            });
            """,
            callback=CheckoutState.receive_gps,
        )

    @rx.event(background=True)
    async def receive_gps(self, result):
        if not result or (
            isinstance(result, list) and len(result) > 0 and (result[0] == "error")
        ):
            async with self:
                self.is_gps_loading = False
                self.geocode_status = ""
                err = (
                    result[1]
                    if isinstance(result, list) and len(result) > 1
                    else "Unknown error"
                )
                self.address_error = (
                    f"GPS failed: {err}. Please enter address manually."
                )
            return
        lat, lon = (float(result[0]), float(result[1]))
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={"lat": lat, "lon": lon, "format": "json"},
                    headers={"User-Agent": "MediSmart/1.0"},
                    timeout=10.0,
                )
                data = resp.json()
                address = data.get("address", {})
                display = data.get("display_name", "Your Location")
                async with self:
                    self.user_lat = lat
                    self.user_lng = lon
                    self.user_address_resolved = display
                    self.has_user_location = True
                    self.is_gps_loading = False
                    self.geocode_status = ""
                    self.house_no = address.get("house_number", "")
                    self.area = (
                        address.get("road", "")
                        or address.get("suburb", "")
                        or address.get("neighbourhood", "")
                    )
                    self.landmark = address.get("suburb", "") or address.get(
                        "city_district", ""
                    )
                    self.pincode = address.get("postcode", "")
                    center_lat = (self.shop_lat + lat) / 2
                    center_lng = (self.shop_lng + lon) / 2
                    self.map_center = latlng(lat=center_lat, lng=center_lng)
                    dist = self.delivery_distance_km
                    if dist < 2:
                        self.map_zoom = 14.0
                    elif dist < 5:
                        self.map_zoom = 13.0
                    elif dist < 15:
                        self.map_zoom = 12.0
                    elif dist < 50:
                        self.map_zoom = 10.0
                    else:
                        self.map_zoom = 8.0
                    self._generate_route_points()
                    yield rx.toast(
                        "📍 Location detected! Address auto-filled.", duration=3000
                    )
        except Exception:
            logging.exception("Reverse geocode error")
            async with self:
                self.user_lat = lat
                self.user_lng = lon
                self.user_address_resolved = f"{lat:.4f}, {lon:.4f}"
                self.has_user_location = True
                self.is_gps_loading = False
                self.geocode_status = ""
                center_lat = (self.shop_lat + lat) / 2
                center_lng = (self.shop_lng + lon) / 2
                self.map_center = latlng(lat=center_lat, lng=center_lng)
                self.map_zoom = 12.0
                self._generate_route_points()

    @rx.event
    def submit_order(self):
        """Save order with address + coordinates."""
        if not self.has_user_location:
            self.address_error = "Please set your delivery address first."
            return
        self.order_loading = True
        yield
        self.saved_order = {
            "address": {
                "house_no": self.house_no,
                "area": self.area,
                "landmark": self.landmark,
                "pincode": self.pincode,
                "full_address": self.full_address,
                "resolved_address": self.user_address_resolved,
                "lat": self.user_lat,
                "lng": self.user_lng,
            },
            "shop": {
                "name": self.shop_name,
                "address": self.shop_address,
                "lat": self.shop_lat,
                "lng": self.shop_lng,
            },
            "items": self.cart_items,
            "total": self.cart_total,
            "distance_km": self.delivery_distance_km,
            "estimated_delivery": self.estimated_delivery_time,
        }
        self.order_submitted = True
        self.order_loading = False
        yield rx.toast(
            "🎉 Order placed successfully! Your medicines are on the way.",
            duration=5000,
        )

    @rx.event
    def reset_checkout(self):
        self.house_no = ""
        self.area = ""
        self.landmark = ""
        self.pincode = ""
        self.address_error = ""
        self.user_lat = 0.0
        self.user_lng = 0.0
        self.user_address_resolved = ""
        self.has_user_location = False
        self.route_positions = []
        self.order_submitted = False
        self.saved_order = {}
        self.map_center = latlng(lat=22.8046, lng=86.2029)
        self.map_zoom = 13.0

    @rx.event
    def clear_user_location(self):
        self.has_user_location = False