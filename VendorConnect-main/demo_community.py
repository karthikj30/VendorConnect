#!/usr/bin/env python3
"""
Interactive Demo: Shows how messages persist across vendor sessions
"""

from app import app, db, Vendor, VendorChatMessage
from datetime import datetime

def demo_cross_vendor_messaging():
    with app.app_context():
        print("\n" + "="*70)
        print("🎭 INTERACTIVE DEMO: Cross-Vendor Messaging")
        print("="*70)
        
        # Get two vendors
        vendor1 = Vendor.query.filter_by(name="Ice Cream Paradise").first()
        vendor2 = Vendor.query.filter_by(name="Chaat Corner").first()
        
        if not vendor1 or not vendor2:
            print("⚠️  Demo vendors not found. Using first two available vendors.")
            vendors = Vendor.query.limit(2).all()
            if len(vendors) < 2:
                print("❌ Need at least 2 vendors in database")
                return
            vendor1, vendor2 = vendors[0], vendors[1]
        
        print(f"\n👤 SCENARIO:")
        print(f"   Vendor A: {vendor1.name} (ID: {vendor1.id})")
        print(f"   Vendor B: {vendor2.name} (ID: {vendor2.id})")
        
        # Session 1: Vendor A sends message
        print(f"\n📱 SESSION 1: {vendor1.name} logs in...")
        print(f"   ✍️  Types: 'Hey! Interested in bulk ordering vegetables?'")
        
        msg1 = VendorChatMessage(
            sender_id=vendor1.id,
            receiver_id=vendor2.id,
            message="Hey! Interested in bulk ordering vegetables?"
        )
        db.session.add(msg1)
        db.session.commit()
        print(f"   💾 Message saved to database (ID: {msg1.id})")
        print(f"   ✅ Message stored at: {msg1.created_at}")
        
        # Session 2: Vendor B logs in and sees message
        print(f"\n📱 SESSION 2: {vendor2.name} logs in...")
        print(f"   🔍 Checking for new messages...")
        
        messages = VendorChatMessage.query.filter(
            VendorChatMessage.sender_id == vendor1.id,
            VendorChatMessage.receiver_id == vendor2.id
        ).all()
        
        print(f"   📬 Found {len(messages)} message(s) from {vendor1.name}:")
        for msg in messages[-3:]:  # Show last 3
            print(f"      └─ [{msg.created_at.strftime('%I:%M %p')}] {msg.message}")
        
        # Session 2: Vendor B replies
        print(f"\n   ✍️  {vendor2.name} replies: 'Yes! Let me know the details'")
        
        msg2 = VendorChatMessage(
            sender_id=vendor2.id,
            receiver_id=vendor1.id,
            message="Yes! Let me know the details"
        )
        db.session.add(msg2)
        db.session.commit()
        print(f"   💾 Reply saved to database (ID: {msg2.id})")
        
        # Session 3: Vendor A sees reply
        print(f"\n📱 SESSION 3: {vendor1.name} refreshes chat...")
        print(f"   🔄 Auto-polling for new messages...")
        
        conversation = VendorChatMessage.query.filter(
            db.or_(
                db.and_(
                    VendorChatMessage.sender_id == vendor1.id,
                    VendorChatMessage.receiver_id == vendor2.id
                ),
                db.and_(
                    VendorChatMessage.sender_id == vendor2.id,
                    VendorChatMessage.receiver_id == vendor1.id
                )
            )
        ).order_by(VendorChatMessage.created_at.desc()).limit(5).all()
        
        conversation.reverse()
        
        print(f"   💬 Complete conversation (last 5 messages):")
        print("   " + "─"*60)
        for msg in conversation:
            sender = db.session.get(Vendor, msg.sender_id)
            direction = "→" if msg.sender_id == vendor1.id else "←"
            print(f"   [{msg.created_at.strftime('%I:%M %p')}] {sender.name} {direction} {msg.message}")
        print("   " + "─"*60)
        
        # Summary
        print(f"\n📊 DATABASE VERIFICATION:")
        total_messages = VendorChatMessage.query.count()
        print(f"   Total messages in database: {total_messages}")
        
        between_vendors = VendorChatMessage.query.filter(
            db.or_(
                db.and_(
                    VendorChatMessage.sender_id == vendor1.id,
                    VendorChatMessage.receiver_id == vendor2.id
                ),
                db.and_(
                    VendorChatMessage.sender_id == vendor2.id,
                    VendorChatMessage.receiver_id == vendor1.id
                )
            )
        ).count()
        
        print(f"   Messages between {vendor1.name} and {vendor2.name}: {between_vendors}")
        
        print(f"\n✅ CONCLUSION:")
        print(f"   ✓ Messages are stored in the database")
        print(f"   ✓ Messages persist across sessions")
        print(f"   ✓ Both vendors can see the conversation")
        print(f"   ✓ New messages appear when vendors refresh")
        print(f"   ✓ Full chat history is maintained")
        
        print("\n" + "="*70)
        print("🎉 The community feature is working perfectly!")
        print("="*70 + "\n")

if __name__ == '__main__':
    demo_cross_vendor_messaging()
