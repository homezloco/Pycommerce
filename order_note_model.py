class OrderNote(db.Model):
    """Order note model."""
    __tablename__ = "order_notes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=True)
    is_customer_visible = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order = relationship("Order", back_populates="notes")
    
    def __repr__(self):
        return f"<OrderNote {self.id}>"

