SELECT c.phone, m.content, m.createdAt, m.`type`, m.isRead, m.isFromMe, m.isSystem,
       m.whatsappAccId, m.userName, m.isInvitation
FROM `Message` m
LEFT JOIN Room r    ON r.id = m.roomId
LEFT JOIN Contact c ON c.id = r.contactId
WHERE m.createdAt >= CURDATE() - INTERVAL 1 MONTH
  AND m.createdAt <  CURDATE()
  AND m.deletedAt IS NULL;
